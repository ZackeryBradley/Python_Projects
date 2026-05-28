import argparse
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

SEED = 42


# =========================================================
# CONFIG / THRESHOLDS
# =========================================================

@dataclass
class ValidationThresholds:
    freshness_hours_max: float = 24.0
    volume_warning_zscore: float = 2.0
    volume_fail_zscore: float = 3.0
    error_rate_warning_pct: float = 1.0
    error_rate_fail_pct: float = 5.0
    budget_min: int = 100000
    budget_max: int = 1000000
    max_date_sk_gap: int = 365
    processing_latency_warning_sec: float = 1.0
    processing_latency_fail_sec: float = 5.0


EXPECTED_SCHEMA = {
    "campaign_sk": "integer",
    "campaign_id": "string",
    "campaign_name": "string",
    "start_date_sk": "integer",
    "end_date_sk": "integer",
    "campaign_budget": "integer",
}

REQUIRED_COLUMNS = list(EXPECTED_SCHEMA.keys())
EXPECTED_COLUMN_COUNT = len(REQUIRED_COLUMNS)
CAMPAIGN_ID_REGEX = r"^CAMP_\d{3}$"


# =========================================================
# ARGUMENTS / PATH HELPERS
# =========================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ultimate automated schema checks and data validations framework with native Excel dashboard charts."
    )
    parser.add_argument(
        "--source-file",
        default="dim_campaigns_schema_data_validation_checks_ts.csv",
        help="Path to the source CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to save outputs. Defaults to current working directory.",
    )
    return parser.parse_args()


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_safe_output_dir(user_output_dir: Optional[str] = None) -> Path:
    """
    Returns a safe absolute output directory.

    If user_output_dir is None or '.', default to a short 'out' folder
    next to the script to reduce Windows path-length issues.
    """
    script_dir = Path(__file__).resolve().parent

    if not user_output_dir or str(user_output_dir).strip() in {"", "."}:
        output_dir = script_dir / "out"
    else:
        output_dir = Path(user_output_dir).expanduser()
        if not output_dir.is_absolute():
            output_dir = script_dir / output_dir

    ensure_directory(output_dir)
    return output_dir


def copy_to_downloads(path: Path) -> Optional[Path]:
    downloads = Path.home() / "Downloads"
    try:
        ensure_directory(downloads)
        target = downloads / path.name
        shutil.copy2(path, target)
        return target
    except Exception:
        return None


def build_short_base_name(source_name: str, timestamp: str) -> str:
    """
    Builds a shorter output base name to prevent Windows path-length issues.
    """
    stem = Path(source_name).stem.lower()

    if "dim_campaigns" in stem:
        short_stem = "dim_campaigns"
    else:
        short_stem = Path(source_name).stem[:20]

    return f"schema_val_{short_stem}_{timestamp}"


# =========================================================
# GENERAL HELPERS
# =========================================================

def status_from_rate(
    fail_count: int,
    total_count: int,
    warning_pct: float = 0.0,
    fail_pct: float = 0.0
) -> str:
    if total_count <= 0:
        return "PASS" if fail_count == 0 else "FAIL"

    pct = (fail_count / total_count) * 100

    if fail_count == 0:
        return "PASS"

    if fail_pct > 0 and pct >= fail_pct:
        return "FAIL"

    if warning_pct > 0 and pct >= warning_pct:
        return "WARNING"

    return "FAIL"


def infer_expected_type(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "string"


# =========================================================
# DATA LOAD / SYNTHETIC REFERENCE TABLES
# =========================================================

def load_source(source_path: Path) -> Tuple[pd.DataFrame, Dict]:
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    df = pd.read_csv(source_path)
    df.columns = [c.strip() for c in df.columns]

    meta = {
        "file_name": source_path.name,
        "last_modified": datetime.fromtimestamp(source_path.stat().st_mtime),
        "loaded_at": datetime.now(),
    }
    return df, meta


def build_reference_tables(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Build synthetic reference structures so the framework can demonstrate:
    - referential integrity against a date dimension
    - historical volume anomaly checks
    - cross-table aggregate reconciliation
    """
    rng = np.random.default_rng(SEED)

    max_date_sk = int(max(df["start_date_sk"].max(), df["end_date_sk"].max(), 365))

    date_dim = pd.DataFrame({
        "date_sk": np.arange(1, max_date_sk + 1, dtype=int),
        "calendar_date": pd.date_range("2025-01-01", periods=max_date_sk, freq="D"),
    })

    current_count = len(df)
    historical_counts = np.rint(rng.normal(loc=current_count, scale=2.2, size=12)).astype(int)
    historical_counts = np.clip(historical_counts, max(current_count - 6, 1), current_count + 6)

    hist_months = pd.date_range(
        end=pd.Timestamp.today().normalize().to_period("M").to_timestamp("M"),
        periods=12,
        freq="ME"
    )

    historical_volume = pd.DataFrame({
        "snapshot_month": hist_months,
        "record_count": historical_counts,
    })

    target_snapshot = df.copy()
    target_snapshot["campaign_budget_target"] = target_snapshot["campaign_budget"]
    target_snapshot["campaign_duration_days"] = (
        target_snapshot["end_date_sk"] - target_snapshot["start_date_sk"]
    )

    budget_recon = target_snapshot.groupby("campaign_id", as_index=False).agg(
        source_budget=("campaign_budget", "sum"),
        target_budget=("campaign_budget_target", "sum"),
        duration_days=("campaign_duration_days", "max"),
    )

    return {
        "date_dim": date_dim,
        "historical_volume": historical_volume,
        "target_snapshot": target_snapshot,
        "budget_recon": budget_recon,
    }


# =========================================================
# CHECKS: STRUCTURAL / SCHEMA
# =========================================================

def run_structural_checks(
    df: pd.DataFrame,
    issue_rows: List[Dict]
) -> Tuple[List[Dict], pd.DataFrame]:
    checks: List[Dict] = []

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    unexpected_columns = [c for c in df.columns if c not in REQUIRED_COLUMNS]

    # Column existence
    checks.append({
        "Category": "Structural & Schema Integrity",
        "CheckName": "Column Existence",
        "Status": "PASS" if not missing_columns else "FAIL",
        "FailedCount": len(missing_columns),
        "FailurePct": round((len(missing_columns) / EXPECTED_COLUMN_COUNT) * 100, 2),
        "Severity": "HIGH" if missing_columns else "INFO",
        "Details": (
            "All required columns are present."
            if not missing_columns
            else f"Missing columns: {missing_columns}"
        ),
    })

    for col in missing_columns:
        issue_rows.append({
            "Category": "Structural & Schema Integrity",
            "CheckName": "Column Existence",
            "RecordIdentifier": None,
            "ColumnName": col,
            "ObservedValue": "MISSING",
            "ExpectedValue": "Column must exist",
            "Severity": "HIGH",
            "IssueMessage": f"Required column '{col}' is missing from the dataset.",
        })

    # Column count
    if unexpected_columns:
        for col in unexpected_columns:
            issue_rows.append({
                "Category": "Structural & Schema Integrity",
                "CheckName": "Column Count",
                "RecordIdentifier": None,
                "ColumnName": col,
                "ObservedValue": "Unexpected column present",
                "ExpectedValue": "No additional columns",
                "Severity": "MEDIUM",
                "IssueMessage": f"Unexpected column '{col}' detected in the dataset.",
            })

    checks.append({
        "Category": "Structural & Schema Integrity",
        "CheckName": "Column Count",
        "Status": "PASS" if len(df.columns) == EXPECTED_COLUMN_COUNT else "FAIL",
        "FailedCount": abs(len(df.columns) - EXPECTED_COLUMN_COUNT),
        "FailurePct": round((abs(len(df.columns) - EXPECTED_COLUMN_COUNT) / EXPECTED_COLUMN_COUNT) * 100, 2),
        "Severity": "HIGH" if len(df.columns) != EXPECTED_COLUMN_COUNT else "INFO",
        "Details": f"Observed {len(df.columns)} columns; expected {EXPECTED_COLUMN_COUNT}.",
    })

    # Data type compliance
    dtype_rows = []
    dtype_fail_count = 0

    for col in REQUIRED_COLUMNS:
        observed = infer_expected_type(df[col]) if col in df.columns else "missing"
        expected = EXPECTED_SCHEMA[col]
        compliant = observed == expected

        dtype_rows.append({
            "ColumnName": col,
            "ExpectedType": expected,
            "ObservedType": observed,
            "Compliant": compliant,
        })

        if not compliant:
            dtype_fail_count += 1
            issue_rows.append({
                "Category": "Structural & Schema Integrity",
                "CheckName": "Data Type Compliance",
                "RecordIdentifier": None,
                "ColumnName": col,
                "ObservedValue": observed,
                "ExpectedValue": expected,
                "Severity": "HIGH",
                "IssueMessage": f"Column '{col}' has type '{observed}' but expected '{expected}'.",
            })

    checks.append({
        "Category": "Structural & Schema Integrity",
        "CheckName": "Data Type Compliance",
        "Status": "PASS" if dtype_fail_count == 0 else "FAIL",
        "FailedCount": dtype_fail_count,
        "FailurePct": round((dtype_fail_count / EXPECTED_COLUMN_COUNT) * 100, 2),
        "Severity": "HIGH" if dtype_fail_count else "INFO",
        "Details": (
            "Observed dtypes align with the expected schema baseline."
            if dtype_fail_count == 0
            else "One or more columns do not match expected dtype baselines."
        ),
    })

    # Regex / format validation
    regex_failures = (
        df[~df["campaign_id"].astype(str).str.match(CAMPAIGN_ID_REGEX, na=False)]
        if "campaign_id" in df.columns
        else pd.DataFrame()
    )

    for _, row in regex_failures.iterrows():
        issue_rows.append({
            "Category": "Structural & Schema Integrity",
            "CheckName": "Format & Regex Patterns",
            "RecordIdentifier": row.get("campaign_sk"),
            "ColumnName": "campaign_id",
            "ObservedValue": row["campaign_id"],
            "ExpectedValue": "Pattern CAMP_###",
            "Severity": "MEDIUM",
            "IssueMessage": "campaign_id does not match the expected structural pattern CAMP_###.",
        })

    checks.append({
        "Category": "Structural & Schema Integrity",
        "CheckName": "Format & Regex Patterns",
        "Status": (
            "PASS"
            if regex_failures.empty
            else status_from_rate(len(regex_failures), len(df), warning_pct=0.1, fail_pct=1.0)
        ),
        "FailedCount": len(regex_failures),
        "FailurePct": round((len(regex_failures) / len(df)) * 100, 2) if len(df) else 0,
        "Severity": "MEDIUM" if len(regex_failures) else "INFO",
        "Details": (
            "campaign_id matches the CAMP_### naming standard."
            if regex_failures.empty
            else f"{len(regex_failures)} campaign_id values failed the regex rule."
        ),
    })

    schema_baseline_df = pd.DataFrame(dtype_rows)
    return checks, schema_baseline_df


# =========================================================
# CHECKS: VOLUME / TIMELINESS
# =========================================================

def run_volume_timeliness_checks(
    df: pd.DataFrame,
    meta: Dict,
    ref: Dict[str, pd.DataFrame],
    issue_rows: List[Dict],
    thresholds: ValidationThresholds
) -> Tuple[List[Dict], pd.DataFrame]:
    checks: List[Dict] = []
    hist = ref["historical_volume"].copy()
    target_snapshot = ref["target_snapshot"]

    source_count = len(df)
    target_count = len(target_snapshot)
    count_delta = abs(source_count - target_count)

    checks.append({
        "Category": "Volume & Timeliness",
        "CheckName": "Record Counts",
        "Status": "PASS" if count_delta == 0 else "FAIL",
        "FailedCount": count_delta,
        "FailurePct": round((count_delta / max(source_count, 1)) * 100, 2),
        "Severity": "HIGH" if count_delta else "INFO",
        "Details": f"Source rows={source_count}; target rows={target_count}.",
    })

    if count_delta:
        issue_rows.append({
            "Category": "Volume & Timeliness",
            "CheckName": "Record Counts",
            "RecordIdentifier": None,
            "ColumnName": "row_count",
            "ObservedValue": source_count,
            "ExpectedValue": target_count,
            "Severity": "HIGH",
            "IssueMessage": "Source and target record counts do not match.",
        })

    freshness_hours = round((meta["loaded_at"] - meta["last_modified"]).total_seconds() / 3600, 2)
    freshness_status = (
        "PASS"
        if freshness_hours <= thresholds.freshness_hours_max
        else ("WARNING" if freshness_hours <= thresholds.freshness_hours_max * 2 else "FAIL")
    )

    checks.append({
        "Category": "Volume & Timeliness",
        "CheckName": "Data Freshness",
        "Status": freshness_status,
        "FailedCount": 0 if freshness_status == "PASS" else 1,
        "FailurePct": 0 if freshness_status == "PASS" else 100,
        "Severity": (
            "MEDIUM" if freshness_status == "WARNING"
            else ("HIGH" if freshness_status == "FAIL" else "INFO")
        ),
        "Details": f"File age at run time is {freshness_hours} hours.",
    })

    if freshness_status != "PASS":
        issue_rows.append({
            "Category": "Volume & Timeliness",
            "CheckName": "Data Freshness",
            "RecordIdentifier": None,
            "ColumnName": "file_last_modified",
            "ObservedValue": freshness_hours,
            "ExpectedValue": f"<= {thresholds.freshness_hours_max} hours",
            "Severity": "MEDIUM" if freshness_status == "WARNING" else "HIGH",
            "IssueMessage": "The dataset appears older than the freshness SLA.",
        })

    hist_mean = float(hist["record_count"].mean())
    hist_std = float(hist["record_count"].std(ddof=0)) if len(hist) > 1 else 0.0
    zscore = 0.0 if hist_std == 0 else (source_count - hist_mean) / hist_std

    if abs(zscore) >= thresholds.volume_fail_zscore:
        volume_status = "FAIL"
    elif abs(zscore) >= thresholds.volume_warning_zscore:
        volume_status = "WARNING"
    else:
        volume_status = "PASS"

    checks.append({
        "Category": "Volume & Timeliness",
        "CheckName": "Volume Anomalies",
        "Status": volume_status,
        "FailedCount": 0 if volume_status == "PASS" else 1,
        "FailurePct": 0 if volume_status == "PASS" else 100,
        "Severity": (
            "MEDIUM" if volume_status == "WARNING"
            else ("HIGH" if volume_status == "FAIL" else "INFO")
        ),
        "Details": f"Current rows={source_count}; historical mean={hist_mean:.2f}; z-score={zscore:.2f}.",
    })

    if volume_status != "PASS":
        issue_rows.append({
            "Category": "Volume & Timeliness",
            "CheckName": "Volume Anomalies",
            "RecordIdentifier": None,
            "ColumnName": "row_count",
            "ObservedValue": source_count,
            "ExpectedValue": f"Historical mean approx. {hist_mean:.2f}",
            "Severity": "MEDIUM" if volume_status == "WARNING" else "HIGH",
            "IssueMessage": "Current row volume deviates materially from historical baseline.",
        })

    hist_augmented = pd.concat([
        hist,
        pd.DataFrame({
            "snapshot_month": [meta["loaded_at"].replace(day=1)],
            "record_count": [source_count]
        })
    ], ignore_index=True)

    return checks, hist_augmented


# =========================================================
# CHECKS: CORE QUALITY / RELATIONAL
# =========================================================

def run_quality_and_relational_checks(
    df: pd.DataFrame,
    ref: Dict[str, pd.DataFrame],
    issue_rows: List[Dict],
    thresholds: ValidationThresholds
) -> Tuple[List[Dict], pd.DataFrame]:
    checks: List[Dict] = []
    null_profile_rows: List[Dict] = []
    invalid_row_ids = set()

    # Null rates
    for col in REQUIRED_COLUMNS:
        null_mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        null_count = int(null_mask.sum())
        null_pct = round((null_count / len(df)) * 100, 2) if len(df) else 0

        null_profile_rows.append({
            "ColumnName": col,
            "NullCount": null_count,
            "NullRatePct": null_pct,
        })

        if null_count:
            for _, row in df[null_mask].iterrows():
                issue_rows.append({
                    "Category": "Core Data Quality Dimensions",
                    "CheckName": "Null Rates",
                    "RecordIdentifier": row.get("campaign_sk"),
                    "ColumnName": col,
                    "ObservedValue": None,
                    "ExpectedValue": "Non-null",
                    "Severity": "HIGH",
                    "IssueMessage": f"Mandatory field '{col}' is null or blank.",
                })
                invalid_row_ids.add(row.get("campaign_sk"))

    total_nulls = int(sum(r["NullCount"] for r in null_profile_rows))
    checks.append({
        "Category": "Core Data Quality Dimensions",
        "CheckName": "Null Rates",
        "Status": (
            "PASS"
            if total_nulls == 0
            else status_from_rate(total_nulls, len(df) * len(REQUIRED_COLUMNS), warning_pct=0.1, fail_pct=1.0)
        ),
        "FailedCount": total_nulls,
        "FailurePct": round((total_nulls / max(len(df) * len(REQUIRED_COLUMNS), 1)) * 100, 2),
        "Severity": "HIGH" if total_nulls else "INFO",
        "Details": (
            "No nulls detected in mandatory columns."
            if total_nulls == 0
            else "One or more mandatory columns contain null or blank values."
        ),
    })

    # Uniqueness
    duplicate_sk = df[df.duplicated(subset=["campaign_sk"], keep=False)]
    duplicate_id = df[df.duplicated(subset=["campaign_id"], keep=False)]
    all_dupes = pd.concat(
        [duplicate_sk.assign(_key="campaign_sk"), duplicate_id.assign(_key="campaign_id")],
        ignore_index=True
    )
    all_dupes = all_dupes.drop_duplicates(subset=["campaign_sk", "_key"]) if not all_dupes.empty else all_dupes

    for _, row in all_dupes.iterrows():
        column_name = row["_key"]
        issue_rows.append({
            "Category": "Core Data Quality Dimensions",
            "CheckName": "Uniqueness",
            "RecordIdentifier": row.get("campaign_sk"),
            "ColumnName": column_name,
            "ObservedValue": row[column_name],
            "ExpectedValue": "Unique value",
            "Severity": "HIGH",
            "IssueMessage": f"Duplicate value detected in '{column_name}'.",
        })
        invalid_row_ids.add(row.get("campaign_sk"))

    checks.append({
        "Category": "Core Data Quality Dimensions",
        "CheckName": "Uniqueness",
        "Status": (
            "PASS"
            if all_dupes.empty
            else status_from_rate(len(all_dupes), len(df), warning_pct=0.1, fail_pct=1.0)
        ),
        "FailedCount": len(all_dupes),
        "FailurePct": round((len(all_dupes) / len(df)) * 100, 2) if len(df) else 0,
        "Severity": "HIGH" if len(all_dupes) else "INFO",
        "Details": (
            "Primary and business keys are unique."
            if all_dupes.empty
            else "Duplicate campaign_sk or campaign_id values were detected."
        ),
    })

    # Range & boundaries
    range_mask = (
        (df["campaign_budget"] < thresholds.budget_min)
        | (df["campaign_budget"] > thresholds.budget_max)
        | (df["start_date_sk"] <= 0)
        | (df["end_date_sk"] <= 0)
        | (df["end_date_sk"] < df["start_date_sk"])
        | ((df["end_date_sk"] - df["start_date_sk"]) > thresholds.max_date_sk_gap)
    )

    range_failures = df[range_mask]

    for _, row in range_failures.iterrows():
        issue_rows.append({
            "Category": "Core Data Quality Dimensions",
            "CheckName": "Range & Boundary Checks",
            "RecordIdentifier": row.get("campaign_sk"),
            "ColumnName": "campaign_budget / start_date_sk / end_date_sk",
            "ObservedValue": f"budget={row['campaign_budget']}, start={row['start_date_sk']}, end={row['end_date_sk']}",
            "ExpectedValue": (
                f"budget {thresholds.budget_min}-{thresholds.budget_max}; "
                f"start <= end and duration <= {thresholds.max_date_sk_gap}"
            ),
            "Severity": "HIGH",
            "IssueMessage": "Campaign fell outside one or more business-logic boundaries.",
        })
        invalid_row_ids.add(row.get("campaign_sk"))

    checks.append({
        "Category": "Core Data Quality Dimensions",
        "CheckName": "Range & Boundary Checks",
        "Status": (
            "PASS"
            if range_failures.empty
            else status_from_rate(len(range_failures), len(df), warning_pct=0.1, fail_pct=1.0)
        ),
        "FailedCount": len(range_failures),
        "FailurePct": round((len(range_failures) / len(df)) * 100, 2) if len(df) else 0,
        "Severity": "HIGH" if len(range_failures) else "INFO",
        "Details": (
            "All budgets and surrogate keys fall within defined boundaries."
            if range_failures.empty
            else "One or more rows violate budget or date-sk business bounds."
        ),
    })

    # Referential integrity
    date_dim = ref["date_dim"]
    valid_keys = set(date_dim["date_sk"].tolist())
    orphan_mask = (~df["start_date_sk"].isin(valid_keys)) | (~df["end_date_sk"].isin(valid_keys))
    orphan_rows = df[orphan_mask]

    for _, row in orphan_rows.iterrows():
        missing_refs = []
        if row["start_date_sk"] not in valid_keys:
            missing_refs.append(f"start_date_sk={row['start_date_sk']}")
        if row["end_date_sk"] not in valid_keys:
            missing_refs.append(f"end_date_sk={row['end_date_sk']}")

        issue_rows.append({
            "Category": "Relational & Cross-Table Integrity",
            "CheckName": "Referential Integrity",
            "RecordIdentifier": row.get("campaign_sk"),
            "ColumnName": "start_date_sk / end_date_sk",
            "ObservedValue": ", ".join(missing_refs),
            "ExpectedValue": "Surrogate key must exist in date dimension",
            "Severity": "HIGH",
            "IssueMessage": "One or more date surrogate keys did not map to the synthetic date dimension.",
        })
        invalid_row_ids.add(row.get("campaign_sk"))

    checks.append({
        "Category": "Relational & Cross-Table Integrity",
        "CheckName": "Referential Integrity",
        "Status": (
            "PASS"
            if orphan_rows.empty
            else status_from_rate(len(orphan_rows), len(df), warning_pct=0.1, fail_pct=1.0)
        ),
        "FailedCount": len(orphan_rows),
        "FailurePct": round((len(orphan_rows) / len(df)) * 100, 2) if len(df) else 0,
        "Severity": "HIGH" if len(orphan_rows) else "INFO",
        "Details": (
            "All date surrogate keys mapped to the reference date dimension."
            if orphan_rows.empty
            else "Unmatched start or end date surrogate keys were detected."
        ),
    })

    # Cross-table consistency
    budget_recon = ref["budget_recon"]
    recon_diff = budget_recon[
        np.round(budget_recon["source_budget"], 2) != np.round(budget_recon["target_budget"], 2)
    ]

    for _, row in recon_diff.iterrows():
        issue_rows.append({
            "Category": "Relational & Cross-Table Integrity",
            "CheckName": "Cross-Table Consistency",
            "RecordIdentifier": row.get("campaign_id"),
            "ColumnName": "campaign_budget",
            "ObservedValue": row["source_budget"],
            "ExpectedValue": row["target_budget"],
            "Severity": "HIGH",
            "IssueMessage": "Budget reconciliation failed between the source dimension and synthetic target audit table.",
        })

    checks.append({
        "Category": "Relational & Cross-Table Integrity",
        "CheckName": "Cross-Table Consistency",
        "Status": (
            "PASS"
            if recon_diff.empty
            else status_from_rate(len(recon_diff), len(budget_recon), warning_pct=0.1, fail_pct=1.0)
        ),
        "FailedCount": len(recon_diff),
        "FailurePct": round((len(recon_diff) / len(budget_recon)) * 100, 2) if len(budget_recon) else 0,
        "Severity": "HIGH" if len(recon_diff) else "INFO",
        "Details": (
            "Cross-table budget totals reconcile cleanly."
            if recon_diff.empty
            else "Source and target aggregate values differ for one or more campaigns."
        ),
    })

    # Error rate
    row_error_rate = round((len(invalid_row_ids) / len(df)) * 100, 2) if len(df) else 0
    error_status = (
        "PASS"
        if row_error_rate == 0
        else ("WARNING" if row_error_rate < thresholds.error_rate_fail_pct else "FAIL")
    )

    checks.append({
        "Category": "Pipeline Observability Metrics",
        "CheckName": "Error Rate",
        "Status": error_status,
        "FailedCount": len(invalid_row_ids),
        "FailurePct": row_error_rate,
        "Severity": (
            "MEDIUM" if error_status == "WARNING"
            else ("HIGH" if error_status == "FAIL" else "INFO")
        ),
        "Details": f"{len(invalid_row_ids)} unique campaign rows failed one or more row-level validations.",
    })

    null_profile_df = pd.DataFrame(null_profile_rows)
    return checks, null_profile_df


# =========================================================
# LATENCY / INSIGHTS
# =========================================================

def build_latency_df(step_timings: Dict[str, float]) -> pd.DataFrame:
    total = sum(step_timings.values())
    rows = []
    for step, elapsed in step_timings.items():
        rows.append({
            "Step": step,
            "LatencySeconds": round(elapsed, 4),
            "SharePct": round((elapsed / total) * 100, 2) if total else 0.0,
        })
    return pd.DataFrame(rows)


def build_insights(
    summary_df: pd.DataFrame,
    issue_details_df: pd.DataFrame,
    hist_volume_df: pd.DataFrame,
    latency_df: pd.DataFrame,
    meta: Dict
) -> List[str]:
    findings = summary_df.set_index("CheckName")

    record_count_line = (
        f"The dataset contains {int(hist_volume_df.iloc[-1]['record_count'])} campaign records "
        f"and {EXPECTED_COLUMN_COUNT} expected columns, providing a stable schema footprint for the current run."
    )
    freshness_line = findings.loc["Data Freshness", "Details"]
    duplicate_line = findings.loc["Uniqueness", "Details"]
    null_line = findings.loc["Null Rates", "Details"]
    regex_line = findings.loc["Format & Regex Patterns", "Details"]

    latency_top = latency_df.sort_values("LatencySeconds", ascending=False).head(2)
    latency_line = (
        "Top latency contributors were "
        + ", ".join([f"{r.Step} ({r.LatencySeconds:.4f}s)" for r in latency_top.itertuples(index=False)])
        + "."
    )

    category_summary = summary_df.groupby("Category", as_index=False).agg(
        FailedChecks=("Status", lambda s: int((s == "FAIL").sum())),
        WarningChecks=("Status", lambda s: int((s == "WARNING").sum())),
    )

    category_line = (
        "Validation domain summary: "
        + ", ".join([
            f"{r.Category} -> {r.FailedChecks} fails / {r.WarningChecks} warnings"
            for r in category_summary.itertuples(index=False)
        ])
        + "."
    )

    if issue_details_df.empty:
        issue_line = (
            "No row-level issues were detected; the sample dataset appears structurally clean "
            "and internally consistent against the configured controls."
        )
    else:
        top_issue_categories = issue_details_df.groupby("CheckName").size().sort_values(ascending=False).head(3)
        issue_line = (
            "Most frequent issue categories: "
            + ", ".join([f"{name} ({count})" for name, count in top_issue_categories.items()])
            + "."
        )

    return [
        f"Validation run timestamp: {meta['loaded_at'].strftime('%Y-%m-%d %H:%M:%S')}.",
        record_count_line,
        freshness_line,
        null_line,
        duplicate_line,
        regex_line,
        category_line,
        issue_line,
        latency_line,
    ]


# =========================================================
# EXCEL DASHBOARD (NATIVE CHARTS)
# =========================================================

def create_dashboard_workbook(
    excel_path: Path,
    summary_df: pd.DataFrame,
    issue_details_df: pd.DataFrame,
    schema_baseline_df: pd.DataFrame,
    null_profile_df: pd.DataFrame,
    hist_volume_df: pd.DataFrame,
    latency_df: pd.DataFrame,
    insights: List[str],
) -> None:
    with pd.ExcelWriter(excel_path, engine="xlsxwriter", datetime_format="yyyy-mm-dd hh:mm:ss") as writer:
        summary_df.to_excel(writer, sheet_name="Validation Summary", index=False)
        issue_details_df.to_excel(writer, sheet_name="Issue Details", index=False)
        schema_baseline_df.to_excel(writer, sheet_name="Schema Baseline", index=False)
        null_profile_df.to_excel(writer, sheet_name="Null Profile", index=False)
        hist_volume_df.to_excel(writer, sheet_name="Historical Volume", index=False)
        latency_df.to_excel(writer, sheet_name="Latency", index=False)
        pd.DataFrame({"Insight": insights}).to_excel(writer, sheet_name="Insights", index=False)

        # Helper data for native Excel charts
        status_counts = summary_df.groupby("Status", as_index=False).size().rename(columns={"size": "CheckCount"})
        by_category = summary_df.groupby(["Category", "Status"], as_index=False).size().rename(columns={"size": "CheckCount"})
        dashboard_data_ws = "DashboardData"

        status_counts.to_excel(writer, sheet_name=dashboard_data_ws, index=False, startrow=0)
        by_category.to_excel(writer, sheet_name=dashboard_data_ws, index=False, startrow=10)
        null_profile_df.to_excel(writer, sheet_name=dashboard_data_ws, index=False, startrow=30)
        hist_volume_df.to_excel(writer, sheet_name=dashboard_data_ws, index=False, startrow=50)
        latency_df.to_excel(writer, sheet_name=dashboard_data_ws, index=False, startrow=70)

        workbook = writer.book
        ws_dash = workbook.add_worksheet("Dashboard")
        writer.sheets["Dashboard"] = ws_dash
        writer.sheets[dashboard_data_ws].hide()
        ws_dash.hide_gridlines(2)

        title_fmt = workbook.add_format({
            "bold": True, "font_size": 18, "font_color": "#FFFFFF",
            "bg_color": "#17375E", "align": "left", "valign": "vcenter"
        })
        section_fmt = workbook.add_format({
            "bold": True, "font_size": 12, "font_color": "#FFFFFF",
            "bg_color": "#1F4E78", "align": "left", "valign": "vcenter"
        })
        header_fmt = workbook.add_format({
            "bold": True, "font_color": "#FFFFFF",
            "bg_color": "#1F4E78", "align": "center", "valign": "vcenter", "border": 1
        })
        card_blue = workbook.add_format({
            "bg_color": "#DCE6F1", "align": "center", "valign": "vcenter", "border": 1, "bold": True
        })
        card_green = workbook.add_format({
            "bg_color": "#E2F0D9", "align": "center", "valign": "vcenter", "border": 1, "bold": True
        })
        card_gold = workbook.add_format({
            "bg_color": "#FFF2CC", "align": "center", "valign": "vcenter", "border": 1, "bold": True
        })
        card_red = workbook.add_format({
            "bg_color": "#FDE9E7", "align": "center", "valign": "vcenter", "border": 1, "bold": True
        })
        text_wrap_fmt = workbook.add_format({
            "text_wrap": True, "valign": "top", "bg_color": "#F3F6FA", "border": 1
        })
        table_fmt = workbook.add_format({"border": 1, "valign": "top"})

        # Style non-dashboard sheets
        sheet_frames = {
            "Validation Summary": summary_df,
            "Issue Details": issue_details_df,
            "Schema Baseline": schema_baseline_df,
            "Null Profile": null_profile_df,
            "Historical Volume": hist_volume_df,
            "Latency": latency_df,
            "Insights": pd.DataFrame({"Insight": insights}),
        }

        for sheet_name, frame in sheet_frames.items():
            ws = writer.sheets[sheet_name]
            ws.freeze_panes(1, 0)
            ws.set_row(0, 24)

            for cidx, cname in enumerate(frame.columns):
                ws.write(0, cidx, cname, header_fmt)
                width = min(max(len(str(cname)) + 2, 12), 38)
                if not frame.empty:
                    try:
                        width = min(max(max(width, frame[cname].astype(str).map(len).max() + 2), 12), 38)
                    except Exception:
                        pass
                ws.set_column(cidx, cidx, width)

            if sheet_name == "Validation Summary" and not frame.empty:
                status_col = frame.columns.get_loc("Status")
                ws.conditional_format(1, status_col, len(frame), status_col, {
                    "type": "text", "criteria": "containing", "value": "PASS",
                    "format": workbook.add_format({"bg_color": "#C6EFCE"})
                })
                ws.conditional_format(1, status_col, len(frame), status_col, {
                    "type": "text", "criteria": "containing", "value": "WARNING",
                    "format": workbook.add_format({"bg_color": "#FFEB9C"})
                })
                ws.conditional_format(1, status_col, len(frame), status_col, {
                    "type": "text", "criteria": "containing", "value": "FAIL",
                    "format": workbook.add_format({"bg_color": "#F4CCCC"})
                })

        # Dashboard layout
        for c in range(14):
            ws_dash.set_column(c, c, 15)

        ws_dash.merge_range("A1:N2", "Schema Checks & Data Validation Dashboard", title_fmt)

        total_rows = int(hist_volume_df.iloc[-1]["record_count"])
        fail_checks = int((summary_df["Status"] == "FAIL").sum())
        warning_checks = int((summary_df["Status"] == "WARNING").sum())
        row_error_rate = float(
            summary_df.loc[summary_df["CheckName"] == "Error Rate", "FailurePct"].iloc[0]
        ) if "Error Rate" in summary_df["CheckName"].values else 0.0

        freshness_text = summary_df.loc[summary_df["CheckName"] == "Data Freshness", "Details"].iloc[0]
        freshness_hours = freshness_text.split("is ")[-1].split(" hours")[0] if "hours" in freshness_text else "0"
        total_latency = latency_df["LatencySeconds"].sum()

        cards = [
            (0, 3, "Total Rows", total_rows, card_blue),
            (3, 3, "Checks Failed", fail_checks, card_red),
            (6, 3, "Checks Warning", warning_checks, card_gold),
            (9, 3, "Error Rate %", round(row_error_rate, 2), card_gold),
            (0, 6, "Freshness Hours", float(freshness_hours), card_green),
            (3, 6, "Schema Columns", EXPECTED_COLUMN_COUNT, card_blue),
            (6, 6, "Issue Rows", len(issue_details_df), card_red),
            (9, 6, "Latency Seconds", round(total_latency, 4), card_green),
        ]

        for col, row, label, value, fmt in cards:
            ws_dash.merge_range(row, col, row, col + 1, label, fmt)
            ws_dash.merge_range(row + 1, col, row + 1, col + 1, value, fmt)

        ws_dash.merge_range("A11:G11", "Executive Insights", section_fmt)
        for idx, line in enumerate(insights[:8], start=12):
            ws_dash.merge_range(idx - 1, 0, idx - 1, 6, line, text_wrap_fmt)
            ws_dash.set_row(idx - 1, 32)

        ws_dash.merge_range("I11:N11", "Top Findings", section_fmt)
        top_findings = summary_df[summary_df["Status"] != "PASS"].copy()
        if top_findings.empty:
            top_findings = summary_df.head(5).copy()
        else:
            top_findings = top_findings.sort_values(["Status", "FailurePct"], ascending=[True, False]).head(6)

        finding_cols = ["Category", "CheckName", "Status", "FailurePct"]
        for cidx, cname in enumerate(finding_cols, start=8):
            ws_dash.write(11, cidx, cname, header_fmt)

        for ridx, row in enumerate(top_findings[finding_cols].itertuples(index=False), start=12):
            for cidx, value in enumerate(row, start=8):
                ws_dash.write(ridx, cidx, value, table_fmt)

        colors = {
            "blue": "#4472C4",
            "orange": "#ED7D31",
            "green": "#70AD47",
            "red": "#C00000",
            "purple": "#7030A0",
        }

        # Chart 1: status counts
        chart1 = workbook.add_chart({"type": "column"})
        status_rows = len(status_counts)
        if status_rows > 0:
            chart1.add_series({
                "name": "Check Count",
                "categories": [dashboard_data_ws, 1, 0, status_rows, 0],
                "values": [dashboard_data_ws, 1, 1, status_rows, 1],
                "fill": {"color": colors["blue"]},
                "border": {"color": colors["blue"]},
                "data_labels": {"value": True},
            })
        chart1.set_title({"name": "Validation Status Count"})
        chart1.set_legend({"none": True})
        chart1.set_size({"width": 560, "height": 280})
        ws_dash.insert_chart("A22", chart1)

        # Chart 2: findings by domain
        categories = sorted(by_category["Category"].unique().tolist())
        helper_start_row = 90
        helper_ws = writer.sheets[dashboard_data_ws]
        helper_ws.write(helper_start_row, 0, "Category")
        helper_ws.write(helper_start_row, 1, "FAIL")
        helper_ws.write(helper_start_row, 2, "WARNING")

        for idx, cat in enumerate(categories, start=1):
            helper_ws.write(helper_start_row + idx, 0, cat)
            fail_count = int(by_category[
                (by_category["Category"] == cat) & (by_category["Status"] == "FAIL")
            ]["CheckCount"].sum())
            warn_count = int(by_category[
                (by_category["Category"] == cat) & (by_category["Status"] == "WARNING")
            ]["CheckCount"].sum())
            helper_ws.write(helper_start_row + idx, 1, fail_count)
            helper_ws.write(helper_start_row + idx, 2, warn_count)

        chart2 = workbook.add_chart({"type": "column", "subtype": "stacked"})
        chart2.add_series({
            "name": [dashboard_data_ws, helper_start_row, 1],
            "categories": [dashboard_data_ws, helper_start_row + 1, 0, helper_start_row + len(categories), 0],
            "values": [dashboard_data_ws, helper_start_row + 1, 1, helper_start_row + len(categories), 1],
            "fill": {"color": colors["red"]},
            "border": {"color": colors["red"]},
        })
        chart2.add_series({
            "name": [dashboard_data_ws, helper_start_row, 2],
            "categories": [dashboard_data_ws, helper_start_row + 1, 0, helper_start_row + len(categories), 0],
            "values": [dashboard_data_ws, helper_start_row + 1, 2, helper_start_row + len(categories), 2],
            "fill": {"color": colors["orange"]},
            "border": {"color": colors["orange"]},
        })
        chart2.set_title({"name": "Findings by Validation Domain"})
        chart2.set_legend({"position": "bottom"})
        chart2.set_size({"width": 560, "height": 280})
        ws_dash.insert_chart("I22", chart2)

        # Chart 3: null profile
        null_rows = len(null_profile_df)
        chart3 = workbook.add_chart({"type": "bar"})
        if null_rows > 0:
            chart3.add_series({
                "name": "Null Rate %",
                "categories": [dashboard_data_ws, 31, 0, 30 + null_rows, 0],
                "values": [dashboard_data_ws, 31, 2, 30 + null_rows, 2],
                "fill": {"color": colors["purple"]},
                "border": {"color": colors["purple"]},
                "data_labels": {"value": True},
            })
        chart3.set_title({"name": "Null Rate by Column"})
        chart3.set_legend({"none": True})
        chart3.set_size({"width": 560, "height": 280})
        ws_dash.insert_chart("A44", chart3)

        # Chart 4: historical volume
        hist_rows = len(hist_volume_df)
        chart4 = workbook.add_chart({"type": "line"})
        chart4.add_series({
            "name": "Record Count",
            "categories": [dashboard_data_ws, 51, 0, 50 + hist_rows, 0],
            "values": [dashboard_data_ws, 51, 1, 50 + hist_rows, 1],
            "line": {"color": colors["green"], "width": 2.0},
            "marker": {
                "type": "circle",
                "size": 5,
                "border": {"color": colors["green"]},
                "fill": {"color": colors["green"]},
            },
        })
        chart4.set_title({"name": "Historical Record Count Trend"})
        chart4.set_x_axis({"date_axis": True, "num_format": "mmm-yy"})
        chart4.set_legend({"none": True})
        chart4.set_size({"width": 560, "height": 280})
        ws_dash.insert_chart("I44", chart4)

        # Chart 5: latency
        lat_rows = len(latency_df)
        chart5 = workbook.add_chart({"type": "column"})
        chart5.add_series({
            "name": "Latency Seconds",
            "categories": [dashboard_data_ws, 71, 0, 70 + lat_rows, 0],
            "values": [dashboard_data_ws, 71, 1, 70 + lat_rows, 1],
            "fill": {"color": colors["orange"]},
            "border": {"color": colors["orange"]},
            "data_labels": {"value": True},
        })
        chart5.set_title({"name": "Processing Latency by Step"})
        chart5.set_legend({"none": True})
        chart5.set_size({"width": 560, "height": 280})
        ws_dash.insert_chart("A66", chart5)


# =========================================================
# EXPORTS
# =========================================================

def write_outputs(
    output_dir: Path,
    source_name: str,
    summary_df: pd.DataFrame,
    issue_details_df: pd.DataFrame,
    schema_baseline_df: pd.DataFrame,
    null_profile_df: pd.DataFrame,
    hist_volume_df: pd.DataFrame,
    latency_df: pd.DataFrame,
    insights: List[str]
) -> Dict[str, Path]:
    ensure_directory(output_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base = build_short_base_name(source_name, timestamp)

    summary_csv = output_dir / f"{base}_summary.csv"
    issues_csv = output_dir / f"{base}_issue_details.csv"
    latency_csv = output_dir / f"{base}_latency.csv"
    nulls_csv = output_dir / f"{base}_null_profile.csv"
    schema_csv = output_dir / f"{base}_schema_baseline.csv"
    volume_csv = output_dir / f"{base}_historical_volume.csv"
    insights_txt = output_dir / f"{base}_insights.txt"
    dashboard_xlsx = output_dir / f"{base}_dashboard.xlsx"

    if issue_details_df is None or issue_details_df.empty:
        issue_details_df = pd.DataFrame(columns=[
            "Category", "CheckName", "RecordIdentifier", "ColumnName",
            "ObservedValue", "ExpectedValue", "Severity", "IssueMessage"
        ])

    try:
        summary_df.to_csv(summary_csv, index=False)
        issue_details_df.to_csv(issues_csv, index=False)
        latency_df.to_csv(latency_csv, index=False)
        null_profile_df.to_csv(nulls_csv, index=False)
        schema_baseline_df.to_csv(schema_csv, index=False)
        hist_volume_df.to_csv(volume_csv, index=False)
        insights_txt.write_text("\n".join(insights), encoding="utf-8")

        create_dashboard_workbook(
            dashboard_xlsx,
            summary_df,
            issue_details_df,
            schema_baseline_df,
            null_profile_df,
            hist_volume_df,
            latency_df,
            insights,
        )

    except OSError:
        # Fallback to a very short path in Downloads
        fallback_dir = Path.home() / "Downloads" / "SchemaValidationOutputs"
        ensure_directory(fallback_dir)

        summary_csv = fallback_dir / f"{base}_summary.csv"
        issues_csv = fallback_dir / f"{base}_issue_details.csv"
        latency_csv = fallback_dir / f"{base}_latency.csv"
        nulls_csv = fallback_dir / f"{base}_null_profile.csv"
        schema_csv = fallback_dir / f"{base}_schema_baseline.csv"
        volume_csv = fallback_dir / f"{base}_historical_volume.csv"
        insights_txt = fallback_dir / f"{base}_insights.txt"
        dashboard_xlsx = fallback_dir / f"{base}_dashboard.xlsx"

        summary_df.to_csv(summary_csv, index=False)
        issue_details_df.to_csv(issues_csv, index=False)
        latency_df.to_csv(latency_csv, index=False)
        null_profile_df.to_csv(nulls_csv, index=False)
        schema_baseline_df.to_csv(schema_csv, index=False)
        hist_volume_df.to_csv(volume_csv, index=False)
        insights_txt.write_text("\n".join(insights), encoding="utf-8")

        create_dashboard_workbook(
            dashboard_xlsx,
            summary_df,
            issue_details_df,
            schema_baseline_df,
            null_profile_df,
            hist_volume_df,
            latency_df,
            insights,
        )

        output_dir = fallback_dir

    outputs = {
        "summary_csv": summary_csv,
        "issues_csv": issues_csv,
        "latency_csv": latency_csv,
        "nulls_csv": nulls_csv,
        "schema_csv": schema_csv,
        "volume_csv": volume_csv,
        "insights_txt": insights_txt,
        "dashboard_xlsx": dashboard_xlsx,
    }

    for key, path in list(outputs.items()):
        downloaded_copy = copy_to_downloads(path)
        if downloaded_copy and downloaded_copy != path:
            outputs[f"{key}_downloads"] = downloaded_copy

    return outputs


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    args = parse_args()
    source_path = Path(args.source_file)
    output_dir = get_safe_output_dir(args.output_dir)
    thresholds = ValidationThresholds()
    issue_rows: List[Dict] = []
    step_timings: Dict[str, float] = {}

    # Load
    t0 = time.perf_counter()
    df, meta = load_source(source_path)
    step_timings["Load Source"] = time.perf_counter() - t0

    # Build references
    t0 = time.perf_counter()
    ref = build_reference_tables(df)
    step_timings["Build Reference Data"] = time.perf_counter() - t0

    # Structural checks
    t0 = time.perf_counter()
    structural_checks, schema_baseline_df = run_structural_checks(df, issue_rows)
    step_timings["Structural Checks"] = time.perf_counter() - t0

    # Volume / timeliness
    t0 = time.perf_counter()
    volume_checks, hist_volume_df = run_volume_timeliness_checks(df, meta, ref, issue_rows, thresholds)
    step_timings["Volume & Timeliness Checks"] = time.perf_counter() - t0

    # Quality / relational
    t0 = time.perf_counter()
    quality_checks, null_profile_df = run_quality_and_relational_checks(df, ref, issue_rows, thresholds)
    step_timings["Quality & Relational Checks"] = time.perf_counter() - t0

    # Assemble summary
    t0 = time.perf_counter()
    summary_df = pd.DataFrame(structural_checks + volume_checks + quality_checks)

    # Add processing latency as an observability check
    interim_total_latency = sum(step_timings.values())
    latency_status = (
        "PASS"
        if interim_total_latency <= thresholds.processing_latency_warning_sec
        else ("WARNING" if interim_total_latency <= thresholds.processing_latency_fail_sec else "FAIL")
    )

    summary_df = pd.concat([
        summary_df,
        pd.DataFrame([{
            "Category": "Pipeline Observability Metrics",
            "CheckName": "Processing Latency",
            "Status": latency_status,
            "FailedCount": 0 if latency_status == "PASS" else 1,
            "FailurePct": 0 if latency_status == "PASS" else 100,
            "Severity": (
                "MEDIUM" if latency_status == "WARNING"
                else ("HIGH" if latency_status == "FAIL" else "INFO")
            ),
            "Details": f"Validation steps completed in {interim_total_latency:.4f} seconds before export.",
        }])
    ], ignore_index=True)

    summary_df["RunTimestamp"] = meta["loaded_at"].strftime("%Y-%m-%d %H:%M:%S")
    ordered_cols = [
        "RunTimestamp", "Category", "CheckName", "Status",
        "FailedCount", "FailurePct", "Severity", "Details"
    ]
    summary_df = summary_df[ordered_cols]

    issue_details_df = pd.DataFrame(issue_rows)
    latency_df = build_latency_df(step_timings)
    insights = build_insights(summary_df, issue_details_df, hist_volume_df, latency_df, meta)
    step_timings["Assemble Outputs"] = time.perf_counter() - t0

    # Export
    t0 = time.perf_counter()
    outputs = write_outputs(
        output_dir,
        source_path.name,
        summary_df,
        issue_details_df,
        schema_baseline_df,
        null_profile_df,
        hist_volume_df,
        latency_df,
        insights,
    )
    step_timings["Export Files"] = time.perf_counter() - t0

    total_seconds = sum(step_timings.values())

    print("\n=============== SCHEMA VALIDATION EXECUTIVE SUMMARY ===============")
    print(f"Run timestamp: {meta['loaded_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Resolved output directory: {output_dir.resolve()}")
    print(f"Source file: {meta['file_name']}")
    print(f"Rows processed: {len(df)}")
    print(f"Checks executed: {len(summary_df)}")
    print(f"Failed checks: {(summary_df['Status'] == 'FAIL').sum()}")
    print(f"Warning checks: {(summary_df['Status'] == 'WARNING').sum()}")

    if "Error Rate" in summary_df["CheckName"].values:
        error_rate = summary_df.loc[summary_df["CheckName"] == "Error Rate", "FailurePct"].iloc[0]
        print(f"Record-level validation error rate: {error_rate:.2f}%")

    print(f"Total processing latency: {total_seconds:.4f} seconds")

    print("\nKey insights:")
    for line in insights[:6]:
        print(f"- {line}")

    print("\nGenerated files:")
    for key, value in outputs.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
