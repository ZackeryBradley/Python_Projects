import argparse
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42


@dataclass
class KPIThresholds:
    min_runway_months: float = 12.0
    max_burn_rate: float = 60.0
    min_clv_cac_ratio: float = 3.0
    max_churn_rate: float = 0.05
    min_nps: float = 25.0
    min_csat: float = 78.0
    max_resolution_hours: float = 24.0
    min_dau_mau_ratio: float = 0.20
    min_conversion_rate: float = 0.02
    max_error_rate_pct: float = 1.75
    max_cycle_time_days: float = 30.0
    min_uptime_pct: float = 99.50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ultimate automated KPI monitoring and alerts generator with native Excel dashboard charts."
    )
    parser.add_argument(
        "--source-file",
        default="Store_CA_KPI_Monitoring.csv",
        help="Path to the source CSV file. Defaults to Store_CA_KPI_Monitoring.csv",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to save primary outputs. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--months-history",
        type=int,
        default=24,
        help="Synthetic monthly history window to assign across records. Defaults to 24 months.",
    )
    return parser.parse_args()


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_to_downloads(file_path: Path) -> Path | None:
    downloads = Path.home() / "Downloads"
    try:
        ensure_directory(downloads)
        target = downloads / file_path.name
        shutil.copy2(file_path, target)
        return target
    except Exception:
        return None


def load_source_data(source_file: Path) -> pd.DataFrame:
    df = pd.read_csv(source_file)
    df.columns = [c.strip() for c in df.columns]
    expected = {
        "ProductVariety", "MarketingSpend", "CustomerFootfall", "StoreSize",
        "EmployeeEfficiency", "StoreAge", "CompetitorDistance", "PromotionsCount",
        "EconomicIndicator", "StoreLocation", "StoreCategory", "MonthlySalesRevenue"
    }
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"Source file is missing required columns: {sorted(missing)}")
    return df


def enrich_dataset(df: pd.DataFrame, months_history: int) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    out = df.copy()
    out.insert(0, "StoreID", [f"STORE-{i:04d}" for i in range(1, len(out) + 1)])

    month_end = pd.Timestamp.today().normalize().to_period("M").to_timestamp("M")
    history = pd.date_range(end=month_end, periods=months_history, freq="ME")
    out["ReportMonth"] = [history[i % months_history] for i in range(len(out))]

    category_recurring_map = {"Electronics": 0.22, "Grocery": 0.48, "Clothing": 0.35}
    margin_map = {"Electronics": 0.34, "Grocery": 0.27, "Clothing": 0.41}
    category_arpu_boost = {"Electronics": 1.20, "Grocery": 0.82, "Clothing": 0.96}

    revenue = out["MonthlySalesRevenue"].astype(float)
    marketing = out["MarketingSpend"].astype(float)
    footfall = out["CustomerFootfall"].astype(float)
    size = out["StoreSize"].astype(float)
    efficiency = out["EmployeeEfficiency"].astype(float)
    age = out["StoreAge"].astype(float)
    comp = out["CompetitorDistance"].astype(float)
    promo = out["PromotionsCount"].astype(float)
    econ = out["EconomicIndicator"].astype(float)
    variety = out["ProductVariety"].astype(float)

    recurring_pct = out["StoreCategory"].map(category_recurring_map).astype(float)
    recurring_pct += np.select([efficiency > 85, efficiency < 60], [0.06, -0.05], default=0.0)
    recurring_pct += np.where(promo >= 7, 0.03, 0)
    recurring_pct = recurring_pct.clip(0.15, 0.70)
    out["RecurringRevenuePct"] = recurring_pct.round(4)
    out["MRR"] = (revenue * recurring_pct).round(2)
    out["RunRateAnnualRevenue"] = (revenue * 12).round(2)

    payroll = (size * 0.11 + (100 - efficiency) * 0.65).round(2)
    rent = (size * out["StoreLocation"].map({"Palo Alto": 0.17, "San Francisco": 0.16, "Los Angeles": 0.15, "Sacramento": 0.12}).astype(float)).round(2)
    techops = (3.8 + (100 - efficiency) * 0.09 + age * 0.13 + rng.uniform(0.2, 1.3, len(out))).round(2)
    support = (2.1 + footfall / 1550 + promo * 0.22).round(2)
    cogs = (revenue * (1 - out["StoreCategory"].map(margin_map).astype(float))).round(2)
    out["PayrollCost"] = payroll
    out["RentCost"] = rent
    out["TechOpsCost"] = techops
    out["SupportOpsCost"] = support
    out["COGS"] = cogs
    out["TotalMonthlyCost"] = (payroll + rent + techops + support + cogs + marketing).round(2)
    out["BurnRate"] = (out["TotalMonthlyCost"] - revenue).clip(lower=0).round(2)

    cash_reserve = (
        revenue * rng.uniform(2.5, 4.5, len(out))
        + size * 0.35
        + efficiency * 0.9
        + np.maximum(comp - 6, 0) * 1.3
    )
    out["CashReserve"] = cash_reserve.round(2)
    runway = np.where(out["BurnRate"] > 0, out["CashReserve"] / out["BurnRate"], np.inf)
    out["RunwayMonths"] = np.where(np.isfinite(runway), np.round(runway, 2), 999.0)

    conversion = (
        0.018
        + 0.00011 * promo
        + 0.00008 * (efficiency - 72)
        + 0.000015 * (variety - 500)
        + 0.0000065 * (econ - 100)
        + 0.00008 * (comp - 10)
        + out["StoreCategory"].map({"Electronics": 0.003, "Grocery": 0.006, "Clothing": 0.004}).astype(float)
    )
    conversion = conversion.clip(0.01, 0.12)
    out["ConversionRate"] = conversion.round(4)

    new_customers = np.maximum(np.floor(footfall * conversion * rng.uniform(0.82, 1.08, len(out))), 1)
    out["NewCustomers"] = new_customers.astype(int)

    active_customers = np.maximum(
        np.floor(footfall * rng.uniform(0.18, 0.32, len(out)) + size * 0.8 + variety * 0.03),
        50,
    )
    out["ActiveCustomers"] = active_customers.astype(int)

    gross_margin = out["StoreCategory"].map(margin_map).astype(float)
    out["GrossMarginPct"] = gross_margin.round(4)
    arpu = ((out["MRR"] * 1000) / out["ActiveCustomers"]).replace([np.inf, -np.inf], np.nan).fillna(0)
    arpu *= out["StoreCategory"].map(category_arpu_boost).astype(float)
    out["ARPU"] = arpu.round(2)

    churn = (
        0.025
        + np.where(comp <= 5, 0.018, np.where(comp >= 14, -0.010, 0))
        + np.where(efficiency < 60, 0.016, np.where(efficiency > 88, -0.010, 0))
        + np.where(econ < 85, 0.012, np.where(econ > 115, -0.006, 0))
        + np.where(promo >= 7, -0.004, 0)
        + out["StoreCategory"].map({"Electronics": 0.004, "Grocery": -0.004, "Clothing": 0.002}).astype(float)
    )
    churn = np.clip(churn, 0.012, 0.14)
    out["ChurnRate"] = np.round(churn, 4)

    cac = (marketing * 1000 / out["NewCustomers"]).clip(lower=50)
    out["CAC"] = np.round(cac, 2)
    clv = np.where(churn > 0, (arpu * gross_margin) / churn, np.nan)
    out["CLV"] = np.round(clv, 2)
    out["CLV_CAC_Ratio"] = np.round(out["CLV"] / out["CAC"], 2)

    nps = (
        35
        + (efficiency - 72) * 0.92
        + (promo - 5) * 1.35
        + (comp - 10) * 0.60
        - (churn * 120)
        + rng.normal(0, 4, len(out))
    )
    out["NPS"] = np.clip(np.round(nps, 1), -10, 88)

    csat = (
        80
        + (efficiency - 72) * 0.33
        + (promo - 5) * 0.95
        + np.where(comp <= 4, -2.0, 0)
        + rng.normal(0, 2.0, len(out))
    )
    out["CSAT"] = np.clip(np.round(csat, 1), 60, 99)

    tickets = np.maximum(np.floor(out["ActiveCustomers"] * rng.uniform(0.018, 0.045, len(out))), 5)
    out["SupportTickets"] = tickets.astype(int)
    resolution = (
        8
        + tickets / 20
        + (100 - efficiency) * 0.14
        + np.where(size > 350, 4.5, 0)
        + np.where(promo >= 7, 1.3, 0)
        + rng.uniform(-1.5, 3.5, len(out))
    )
    out["ResolutionTimeHours"] = np.clip(np.round(resolution, 2), 2, 72)

    dau = np.maximum(np.floor(out["ActiveCustomers"] * rng.uniform(0.18, 0.42, len(out))), 20)
    mau = np.maximum(dau + np.floor(out["ActiveCustomers"] * rng.uniform(0.65, 1.35, len(out))), dau + 1)
    out["DAU"] = dau.astype(int)
    out["MAU"] = mau.astype(int)
    out["DAU_MAU_Ratio"] = np.round(out["DAU"] / out["MAU"], 4)

    error_rate = (
        0.35
        + (100 - efficiency) * 0.018
        + age * 0.025
        + np.where(econ < 80, 0.35, 0)
        + np.where(size > 425, 0.18, 0)
        + rng.uniform(0.0, 0.35, len(out))
    )
    out["ErrorRatePct"] = np.clip(np.round(error_rate, 3), 0.10, 4.25)

    uptime = 99.97 - out["ErrorRatePct"] * 0.235 - np.where(age > 20, 0.08, 0) - np.where(size > 450, 0.06, 0)
    out["SystemUptimePct"] = np.clip(np.round(uptime, 3), 97.30, 99.98)

    cycle = (
        13
        + (variety - 500) / 36
        + np.where(efficiency > 85, -4.0, 0)
        + np.where(size > 380, 4.0, 0)
        + rng.uniform(-2.5, 5.5, len(out))
    )
    out["CycleTimeDays"] = np.clip(np.round(cycle, 1), 5.0, 60.0)
    out["TimeToMarketDays"] = out["CycleTimeDays"]

    out["RevenuePerSqFt"] = np.round(revenue / size, 3)
    out["FootfallPerPromotion"] = np.round(footfall / promo, 2)
    out["RevenuePerEmployeeEfficiencyPoint"] = np.round(revenue / efficiency, 3)

    return out


def build_portfolio_summary(df: pd.DataFrame) -> pd.DataFrame:
    total_revenue = df["MonthlySalesRevenue"].sum()
    total_cost = df["TotalMonthlyCost"].sum()
    total_mrr = df["MRR"].sum()
    weighted_conversion = df["NewCustomers"].sum() / df["CustomerFootfall"].sum()
    weighted_churn = np.average(df["ChurnRate"], weights=df["ActiveCustomers"])
    weighted_nps = np.average(df["NPS"], weights=df["ActiveCustomers"])
    weighted_csat = np.average(df["CSAT"], weights=df["SupportTickets"])
    weighted_dau_mau = df["DAU"].sum() / df["MAU"].sum()
    weighted_error_rate = np.average(df["ErrorRatePct"], weights=df["StoreSize"])
    weighted_uptime = np.average(df["SystemUptimePct"], weights=df["StoreSize"])
    weighted_cycle = np.average(df["CycleTimeDays"], weights=df["ProductVariety"])

    metrics = [
        ("Revenue & Financial Health", "Total Monthly Revenue", total_revenue, "k", "Sum of monthly sales revenue"),
        ("Revenue & Financial Health", "Total Monthly Cost", total_cost, "k", "Estimated operating + support + marketing + COGS"),
        ("Revenue & Financial Health", "Burn Rate", df["BurnRate"].mean(), "k", "Average monthly operating shortfall per store"),
        ("Revenue & Financial Health", "Run Rate", total_revenue * 12, "k", "Annualized revenue run rate"),
        ("Revenue & Financial Health", "MRR", total_mrr, "k", "Recurring revenue modeled from category mix and retention profile"),
        ("Revenue & Financial Health", "CAC", df["CAC"].mean(), "$", "Average customer acquisition cost"),
        ("Revenue & Financial Health", "CLV", df["CLV"].mean(), "$", "Average customer lifetime value"),
        ("Revenue & Financial Health", "CLV/CAC Ratio", df["CLV_CAC_Ratio"].replace([np.inf, -np.inf], np.nan).mean(), "ratio", "Healthy SaaS/recurring benchmark is typically > 3"),
        ("Customer Experience & Retention", "Churn Rate", weighted_churn * 100, "%", "Active-customer-weighted churn rate"),
        ("Customer Experience & Retention", "NPS", weighted_nps, "score", "Net promoter score modeled from service and competitive context"),
        ("Customer Experience & Retention", "CSAT", weighted_csat, "%", "Support-ticket weighted CSAT"),
        ("Customer Experience & Retention", "Resolution Time", df["ResolutionTimeHours"].mean(), "hours", "Average support resolution time"),
        ("Customer Experience & Retention", "DAU/MAU", weighted_dau_mau, "ratio", "Portfolio engagement stickiness"),
        ("Product, Ops & Technical Performance", "Conversion Rate", weighted_conversion * 100, "%", "CustomerFootfall to NewCustomers conversion"),
        ("Product, Ops & Technical Performance", "Error Rate", weighted_error_rate, "%", "Weighted technical error rate"),
        ("Product, Ops & Technical Performance", "Cycle Time", weighted_cycle, "days", "Average time to deliver/store refresh cycles"),
        ("Product, Ops & Technical Performance", "System Uptime", weighted_uptime, "%", "Weighted system availability"),
    ]
    summary = pd.DataFrame(metrics, columns=["KPIGroup", "Metric", "Value", "Unit", "Definition"])
    summary["Value"] = summary["Value"].round(2)
    return summary


def build_segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    seg = (
        df.groupby(["StoreLocation", "StoreCategory"], as_index=False)
        .agg(
            Stores=("StoreID", "count"),
            Revenue=("MonthlySalesRevenue", "sum"),
            MRR=("MRR", "sum"),
            AvgBurnRate=("BurnRate", "mean"),
            AvgRunwayMonths=("RunwayMonths", "mean"),
            AvgCAC=("CAC", "mean"),
            AvgCLV=("CLV", "mean"),
            AvgChurnRate=("ChurnRate", "mean"),
            AvgNPS=("NPS", "mean"),
            AvgCSAT=("CSAT", "mean"),
            AvgResolutionTimeHours=("ResolutionTimeHours", "mean"),
            AvgDAUMAU=("DAU_MAU_Ratio", "mean"),
            AvgConversionRate=("ConversionRate", "mean"),
            AvgErrorRatePct=("ErrorRatePct", "mean"),
            AvgCycleTimeDays=("CycleTimeDays", "mean"),
            AvgSystemUptimePct=("SystemUptimePct", "mean"),
        )
    )
    for col in seg.columns:
        if col not in {"StoreLocation", "StoreCategory", "Stores"}:
            seg[col] = seg[col].round(2)
    seg["CLV_CAC_Ratio"] = (seg["AvgCLV"] / seg["AvgCAC"]).round(2)
    return seg.sort_values(["Revenue", "MRR"], ascending=[False, False])


def build_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    trend = (
        df.groupby("ReportMonth", as_index=False)
        .agg(
            Revenue=("MonthlySalesRevenue", "sum"),
            Cost=("TotalMonthlyCost", "sum"),
            MRR=("MRR", "sum"),
            BurnRate=("BurnRate", "mean"),
            CAC=("CAC", "mean"),
            CLV=("CLV", "mean"),
            ChurnRate=("ChurnRate", "mean"),
            NPS=("NPS", "mean"),
            CSAT=("CSAT", "mean"),
            ResolutionTimeHours=("ResolutionTimeHours", "mean"),
            DAU=("DAU", "sum"),
            MAU=("MAU", "sum"),
            ConversionRate=("ConversionRate", "mean"),
            ErrorRatePct=("ErrorRatePct", "mean"),
            CycleTimeDays=("CycleTimeDays", "mean"),
            SystemUptimePct=("SystemUptimePct", "mean"),
            Alerts=("StoreID", "count"),
        )
    )
    trend["DAU_MAU_Ratio"] = (trend["DAU"] / trend["MAU"]).round(4)
    trend["ReportMonth"] = pd.to_datetime(trend["ReportMonth"])
    for col in trend.columns:
        if col != "ReportMonth":
            trend[col] = trend[col].round(2)
    return trend.sort_values("ReportMonth")


def generate_alerts(df: pd.DataFrame, thresholds: KPIThresholds) -> pd.DataFrame:
    rules = [
        ("Burn Rate", "BurnRate", ">", thresholds.max_burn_rate, "Average monthly burn is above tolerance; review cost structure and working capital."),
        ("Runway Months", "RunwayMonths", "<", thresholds.min_runway_months, "Cash runway is shorter than target; raise margin, cut cost, or increase revenue coverage."),
        ("CLV/CAC Ratio", "CLV_CAC_Ratio", "<", thresholds.min_clv_cac_ratio, "Customer value does not sufficiently exceed acquisition cost."),
        ("Churn Rate", "ChurnRate", ">", thresholds.max_churn_rate, "Retention risk is elevated."),
        ("NPS", "NPS", "<", thresholds.min_nps, "Customer advocacy is below target."),
        ("CSAT", "CSAT", "<", thresholds.min_csat, "Satisfaction is below target."),
        ("Resolution Time", "ResolutionTimeHours", ">", thresholds.max_resolution_hours, "Support queue is slow; staffing or prioritization may be needed."),
        ("DAU/MAU", "DAU_MAU_Ratio", "<", thresholds.min_dau_mau_ratio, "Engagement stickiness is weak."),
        ("Conversion Rate", "ConversionRate", "<", thresholds.min_conversion_rate, "Footfall-to-customer conversion is soft."),
        ("Error Rate", "ErrorRatePct", ">", thresholds.max_error_rate_pct, "Technical reliability risk detected."),
        ("Cycle Time", "CycleTimeDays", ">", thresholds.max_cycle_time_days, "Delivery cycle is slower than target."),
        ("System Uptime", "SystemUptimePct", "<", thresholds.min_uptime_pct, "Availability below SLA target."),
    ]

    alert_frames = []
    for metric_name, column, op, threshold, message in rules:
        if op == ">":
            subset = df[df[column] > threshold].copy()
            if subset.empty:
                continue
            subset["BreachAmount"] = subset[column] - threshold
        else:
            subset = df[df[column] < threshold].copy()
            if subset.empty:
                continue
            subset["BreachAmount"] = threshold - subset[column]

        severity = np.where(
            subset["BreachAmount"] >= np.nanpercentile(subset["BreachAmount"], 75),
            "CRITICAL",
            np.where(subset["BreachAmount"] >= np.nanpercentile(subset["BreachAmount"], 40), "HIGH", "MEDIUM"),
        )
        subset_alert = pd.DataFrame({
            "AlertTimestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "StoreID": subset["StoreID"],
            "ReportMonth": subset["ReportMonth"].dt.strftime("%Y-%m-%d"),
            "StoreLocation": subset["StoreLocation"],
            "StoreCategory": subset["StoreCategory"],
            "Metric": metric_name,
            "ObservedValue": subset[column].round(4),
            "Threshold": threshold,
            "Operator": op,
            "BreachAmount": subset["BreachAmount"].round(4),
            "Severity": severity,
            "RecommendedAction": message,
        })
        alert_frames.append(subset_alert)

    if not alert_frames:
        return pd.DataFrame(columns=[
            "AlertTimestamp", "StoreID", "ReportMonth", "StoreLocation", "StoreCategory",
            "Metric", "ObservedValue", "Threshold", "Operator", "BreachAmount", "Severity", "RecommendedAction"
        ])

    alerts = pd.concat(alert_frames, ignore_index=True)
    alerts["MetricPriority"] = alerts["Metric"].map({
        "Runway Months": 1, "Burn Rate": 2, "CLV/CAC Ratio": 3, "Churn Rate": 4,
        "System Uptime": 5, "Error Rate": 6, "CSAT": 7, "NPS": 8, "Resolution Time": 9,
        "Conversion Rate": 10, "DAU/MAU": 11, "Cycle Time": 12,
    }).fillna(99)
    severity_order = pd.Categorical(alerts["Severity"], categories=["CRITICAL", "HIGH", "MEDIUM"], ordered=True)
    alerts["Severity"] = severity_order
    alerts = alerts.sort_values(["Severity", "MetricPriority", "BreachAmount"], ascending=[True, True, False]).drop(columns=["MetricPriority"])
    alerts["Severity"] = alerts["Severity"].astype(str)
    return alerts


def build_status_summary(summary: pd.DataFrame, thresholds: KPIThresholds) -> pd.DataFrame:
    status_rows = []
    for row in summary.itertuples(index=False):
        metric = row.Metric
        value = row.Value
        if metric == "Burn Rate":
            status = "PASS" if value <= thresholds.max_burn_rate else ("WARNING" if value <= thresholds.max_burn_rate * 1.15 else "FAIL")
        elif metric == "CLV/CAC Ratio":
            status = "PASS" if value >= thresholds.min_clv_cac_ratio else ("WARNING" if value >= thresholds.min_clv_cac_ratio * 0.85 else "FAIL")
        elif metric == "Churn Rate":
            status = "PASS" if value / 100 <= thresholds.max_churn_rate else ("WARNING" if value / 100 <= thresholds.max_churn_rate * 1.2 else "FAIL")
        elif metric == "NPS":
            status = "PASS" if value >= thresholds.min_nps else ("WARNING" if value >= thresholds.min_nps - 5 else "FAIL")
        elif metric == "CSAT":
            status = "PASS" if value >= thresholds.min_csat else ("WARNING" if value >= thresholds.min_csat - 3 else "FAIL")
        elif metric == "Resolution Time":
            status = "PASS" if value <= thresholds.max_resolution_hours else ("WARNING" if value <= thresholds.max_resolution_hours * 1.2 else "FAIL")
        elif metric == "DAU/MAU":
            status = "PASS" if value >= thresholds.min_dau_mau_ratio else ("WARNING" if value >= thresholds.min_dau_mau_ratio * 0.85 else "FAIL")
        elif metric == "Conversion Rate":
            status = "PASS" if value / 100 >= thresholds.min_conversion_rate else ("WARNING" if value / 100 >= thresholds.min_conversion_rate * 0.85 else "FAIL")
        elif metric == "Error Rate":
            status = "PASS" if value <= thresholds.max_error_rate_pct else ("WARNING" if value <= thresholds.max_error_rate_pct * 1.2 else "FAIL")
        elif metric == "Cycle Time":
            status = "PASS" if value <= thresholds.max_cycle_time_days else ("WARNING" if value <= thresholds.max_cycle_time_days * 1.15 else "FAIL")
        elif metric == "System Uptime":
            status = "PASS" if value >= thresholds.min_uptime_pct else ("WARNING" if value >= thresholds.min_uptime_pct - 0.2 else "FAIL")
        else:
            status = "PASS"
        status_rows.append({
            "KPIGroup": row.KPIGroup,
            "Metric": metric,
            "Value": row.Value,
            "Unit": row.Unit,
            "Status": status,
            "Definition": row.Definition,
        })
    return pd.DataFrame(status_rows)


def build_insights(summary: pd.DataFrame, alerts: pd.DataFrame, segment: pd.DataFrame) -> list[str]:
    val = summary.set_index("Metric")["Value"].to_dict()
    insights = [
        f"Revenue engine: The portfolio is generating {val.get('Total Monthly Revenue', 0):,.2f}k in monthly revenue and {val.get('MRR', 0):,.2f}k in recurring revenue, showing a strong recurring base layered on top of monthly sales.",
        f"Financial health: Average burn rate is {val.get('Burn Rate', 0):,.2f}k per store with an average CLV/CAC ratio of {val.get('CLV/CAC Ratio', 0):.2f}. Customer economics are healthy overall, though weaker segments still need close monitoring.",
        f"Retention posture: Weighted churn is {val.get('Churn Rate', 0):.2f}% and DAU/MAU is {val.get('DAU/MAU', 0):.2f}. Engagement is acceptable, but repeat-usage and loyalty still represent a major optimization lever.",
        f"Experience signal: Weighted NPS is {val.get('NPS', 0):.2f} and CSAT is {val.get('CSAT', 0):.2f}%. Sentiment is stable but not elite, so service quality and store execution remain high-impact levers.",
        f"Reliability signal: Weighted error rate is {val.get('Error Rate', 0):.2f}% while uptime is {val.get('System Uptime', 0):.2f}%. Technical reliability is broadly healthy, but localized incidents can still hurt customer confidence and conversion.",
    ]
    if not alerts.empty:
        top_alerts = alerts.groupby("Metric").size().sort_values(ascending=False).head(5)
        insights.append("Top alert metrics: " + ", ".join([f"{m} ({c})" for m, c in top_alerts.items()]))
    top_segments = segment.nlargest(3, "Revenue")[["StoreLocation", "StoreCategory", "Revenue", "MRR", "AvgNPS", "CLV_CAC_Ratio"]]
    for row in top_segments.itertuples(index=False):
        insights.append(
            f"Top segment: {row.StoreLocation} | {row.StoreCategory} → Revenue {row.Revenue:,.2f}k, MRR {row.MRR:,.2f}k, NPS {row.AvgNPS:.1f}, CLV/CAC {row.CLV_CAC_Ratio:.2f}."
        )
    return insights


def write_dashboard_with_native_charts(
    excel_path: Path,
    status_summary: pd.DataFrame,
    alerts: pd.DataFrame,
    segment: pd.DataFrame,
    trend: pd.DataFrame,
    enriched: pd.DataFrame,
    insights: list[str],
) -> None:
    with pd.ExcelWriter(excel_path, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
        status_summary.to_excel(writer, sheet_name="KPI Summary", index=False)
        alerts.to_excel(writer, sheet_name="Alerts", index=False)
        segment.to_excel(writer, sheet_name="Segment Summary", index=False)
        trend.to_excel(writer, sheet_name="Monthly Trend", index=False)
        enriched.to_excel(writer, sheet_name="Enriched Store KPIs", index=False)

        # Support tables for dashboard visuals
        alert_counts = alerts.groupby("Metric", as_index=False).size().rename(columns={"size": "AlertCount"}) if not alerts.empty else pd.DataFrame({"Metric": [], "AlertCount": []})
        alert_counts.to_excel(writer, sheet_name="DashboardData", index=False, startrow=0)
        insights_df = pd.DataFrame({"Insight": insights})
        insights_df.to_excel(writer, sheet_name="Insights", index=False)

        workbook = writer.book
        ws_dash = workbook.add_worksheet("Dashboard")
        writer.sheets["Dashboard"] = ws_dash
        ws_dash.hide_gridlines(2)

        # Formats
        title_fmt = workbook.add_format({"bold": True, "font_size": 18, "font_color": "#FFFFFF", "bg_color": "#17375E", "align": "left", "valign": "vcenter"})
        section_fmt = workbook.add_format({"bold": True, "font_size": 12, "font_color": "#FFFFFF", "bg_color": "#1F4E78", "align": "left", "valign": "vcenter"})
        header_fmt = workbook.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#1F4E78", "align": "center", "valign": "vcenter", "border": 1})
        card_title_fmt = workbook.add_format({"bold": True, "font_size": 11, "align": "center", "valign": "vcenter", "border": 1})
        card_value_fmt = workbook.add_format({"bold": True, "font_size": 15, "align": "center", "valign": "vcenter", "border": 1})
        card_blue = workbook.add_format({"bg_color": "#DCE6F1", "align": "center", "valign": "vcenter", "border": 1, "bold": True})
        card_green = workbook.add_format({"bg_color": "#E2F0D9", "align": "center", "valign": "vcenter", "border": 1, "bold": True})
        card_gold = workbook.add_format({"bg_color": "#FFF2CC", "align": "center", "valign": "vcenter", "border": 1, "bold": True})
        card_red = workbook.add_format({"bg_color": "#FDE9E7", "align": "center", "valign": "vcenter", "border": 1, "bold": True})
        text_wrap_fmt = workbook.add_format({"text_wrap": True, "valign": "top", "bg_color": "#F3F6FA", "border": 1})
        table_body_fmt = workbook.add_format({"border": 1, "valign": "top"})
        percent_fmt = workbook.add_format({"num_format": '0.00', "align": "center", "valign": "vcenter", "border": 1})
        decimal_fmt = workbook.add_format({"num_format": '0.00', "align": "center", "valign": "vcenter", "border": 1})

        # Style data sheets
        sheet_frames = {
            "KPI Summary": status_summary,
            "Alerts": alerts,
            "Segment Summary": segment,
            "Monthly Trend": trend,
            "Enriched Store KPIs": enriched,
            "Insights": insights_df,
            "DashboardData": alert_counts,
        }
        for sheet_name, frame in sheet_frames.items():
            ws = writer.sheets[sheet_name]
            ws.freeze_panes(1, 0)
            ws.set_row(0, 24)
            for col_idx, col_name in enumerate(frame.columns):
                ws.write(0, col_idx, col_name, header_fmt)
                max_len = max(len(str(col_name)), frame[col_name].astype(str).map(len).max() if not frame.empty else 0)
                ws.set_column(col_idx, col_idx, min(max(max_len + 2, 12), 40))
            if sheet_name == "KPI Summary" and len(frame) > 0:
                status_col = frame.columns.get_loc("Status")
                ws.conditional_format(1, status_col, len(frame), status_col, {
                    'type': 'text', 'criteria': 'containing', 'value': 'PASS',
                    'format': workbook.add_format({'bg_color': '#C6EFCE'})
                })
                ws.conditional_format(1, status_col, len(frame), status_col, {
                    'type': 'text', 'criteria': 'containing', 'value': 'WARNING',
                    'format': workbook.add_format({'bg_color': '#FFEB9C'})
                })
                ws.conditional_format(1, status_col, len(frame), status_col, {
                    'type': 'text', 'criteria': 'containing', 'value': 'FAIL',
                    'format': workbook.add_format({'bg_color': '#F4CCCC'})
                })

        # Hide helper data sheet so visuals still live natively in workbook
        writer.sheets["DashboardData"].hide()

        # Dashboard layout
        ws_dash.merge_range("A1:M2", "Ultimate KPI Monitoring & Alerts Dashboard", title_fmt)
        for c in range(13):
            ws_dash.set_column(c, c, 15)
        ws_dash.set_default_row(20)

        metric_lookup = status_summary.set_index("Metric")["Value"].to_dict()
        cards = [
            (0, 3, "Total Revenue (k)", metric_lookup.get("Total Monthly Revenue", 0), card_blue),
            (3, 3, "Total MRR (k)", metric_lookup.get("MRR", 0), card_green),
            (6, 3, "Avg Burn Rate (k)", metric_lookup.get("Burn Rate", 0), card_gold),
            (9, 3, "Active Alerts", len(alerts), card_red),
            (0, 6, "Churn %", metric_lookup.get("Churn Rate", 0), card_gold),
            (3, 6, "Portfolio NPS", metric_lookup.get("NPS", 0), card_blue),
            (6, 6, "CSAT %", metric_lookup.get("CSAT", 0), card_green),
            (9, 6, "System Uptime %", metric_lookup.get("System Uptime", 0), card_green),
        ]
        for col, row, label, value, fmt in cards:
            ws_dash.merge_range(row, col, row, col + 1, label, fmt)
            ws_dash.merge_range(row + 1, col, row + 1, col + 1, round(float(value), 2), fmt)

        # Executive insights block
        ws_dash.merge_range("A11:F11", "Executive Insights", section_fmt)
        start_row = 11
        for idx, line in enumerate(insights[:9], start=1):
            ws_dash.merge_range(start_row + idx, 0, start_row + idx, 5, line, text_wrap_fmt)
            ws_dash.set_row(start_row + idx, 34)

        # Hotspot table
        ws_dash.merge_range("H11:M11", "Top Alert Hotspots", section_fmt)
        hotspot = segment.sort_values(["AvgBurnRate", "AvgChurnRate", "AvgErrorRatePct"], ascending=False).head(8).copy()
        hotspot_display = hotspot[[
            "StoreLocation", "StoreCategory", "Revenue", "MRR", "AvgBurnRate",
            "AvgChurnRate", "AvgNPS", "AvgSystemUptimePct", "CLV_CAC_Ratio"
        ]]
        hdr_row = 11
        for c_idx, col_name in enumerate(hotspot_display.columns, start=7):
            ws_dash.write(hdr_row + 1, c_idx, col_name, header_fmt)
        for r_idx, row in enumerate(hotspot_display.itertuples(index=False), start=hdr_row + 2):
            for c_idx, value in enumerate(row, start=7):
                ws_dash.write(r_idx, c_idx, value, table_body_fmt)

        # Native Excel charts
        trend_rows = len(trend)
        trend_sheet = "Monthly Trend"
        date_col = 0
        revenue_col = trend.columns.get_loc("Revenue")
        cost_col = trend.columns.get_loc("Cost")
        mrr_col = trend.columns.get_loc("MRR")
        churn_col = trend.columns.get_loc("ChurnRate")
        nps_col = trend.columns.get_loc("NPS")
        csat_col = trend.columns.get_loc("CSAT")
        conv_col = trend.columns.get_loc("ConversionRate")
        error_col = trend.columns.get_loc("ErrorRatePct")
        uptime_col = trend.columns.get_loc("SystemUptimePct")

        colors = {
            'blue': '#4472C4', 'orange': '#ED7D31', 'green': '#70AD47', 'gold': '#FFC000',
            'red': '#C00000', 'teal': '#5B9BD5', 'purple': '#7030A0'
        }

        chart1 = workbook.add_chart({'type': 'line'})
        for name, col, color in [("Revenue", revenue_col, colors['blue']), ("Cost", cost_col, colors['orange']), ("MRR", mrr_col, colors['green'])]:
            chart1.add_series({
                'name':       [trend_sheet, 0, col],
                'categories': [trend_sheet, 1, date_col, trend_rows, date_col],
                'values':     [trend_sheet, 1, col, trend_rows, col],
                'line':       {'color': color, 'width': 2.0},
                'marker':     {'type': 'circle', 'size': 5, 'border': {'color': color}, 'fill': {'color': color}},
            })
        chart1.set_title({'name': 'Revenue, Cost, and MRR Trend'})
        chart1.set_x_axis({'date_axis': True, 'num_format': 'mmm-yy'})
        chart1.set_y_axis({'name': 'Value (k)'})
        chart1.set_legend({'position': 'bottom'})
        chart1.set_size({'width': 600, 'height': 290})
        ws_dash.insert_chart('A30', chart1)

        chart2 = workbook.add_chart({'type': 'line'})
        for name, col, color, scale in [
            ("Churn %", churn_col, colors['red'], 100),
            ("NPS", nps_col, colors['blue'], 1),
            ("CSAT", csat_col, colors['green'], 1),
        ]:
            # For churn %, use helper data in DashboardData if scaling needed
            if scale == 1:
                chart2.add_series({
                    'name': [trend_sheet, 0, col],
                    'categories': [trend_sheet, 1, date_col, trend_rows, date_col],
                    'values': [trend_sheet, 1, col, trend_rows, col],
                    'line': {'color': color, 'width': 2.0},
                    'marker': {'type': 'circle', 'size': 5, 'border': {'color': color}, 'fill': {'color': color}},
                })
            else:
                # write scaled helper column
                helper_ws = writer.sheets['DashboardData']
                base_col_offset = 3
                helper_col = base_col_offset
                helper_ws.write(0, helper_col, 'TrendMonth')
                helper_ws.write(0, helper_col + 1, 'ChurnPct')
                for r in range(trend_rows):
                    helper_ws.write_datetime(r + 1, helper_col, pd.to_datetime(trend.iloc[r, date_col]).to_pydatetime())
                    helper_ws.write_number(r + 1, helper_col + 1, float(trend.iloc[r, col]) * 100)
                chart2.add_series({
                    'name': 'Churn %',
                    'categories': ['DashboardData', 1, helper_col, trend_rows, helper_col],
                    'values': ['DashboardData', 1, helper_col + 1, trend_rows, helper_col + 1],
                    'line': {'color': color, 'width': 2.0},
                    'marker': {'type': 'circle', 'size': 5, 'border': {'color': color}, 'fill': {'color': color}},
                })
        chart2.set_title({'name': 'Customer Experience Trend'})
        chart2.set_x_axis({'date_axis': True, 'num_format': 'mmm-yy'})
        chart2.set_y_axis({'name': 'Value'})
        chart2.set_legend({'position': 'bottom'})
        chart2.set_size({'width': 600, 'height': 290})
        ws_dash.insert_chart('J30', chart2)

        chart3 = workbook.add_chart({'type': 'line'})
        helper_ws = writer.sheets['DashboardData']
        base_col_offset = 6
        helper_headers = ['TrendMonth2', 'ConversionPct', 'ErrorRatePct', 'SystemUptimePct']
        for i, hdr in enumerate(helper_headers):
            helper_ws.write(0, base_col_offset + i, hdr)
        for r in range(trend_rows):
            helper_ws.write_datetime(r + 1, base_col_offset, pd.to_datetime(trend.iloc[r, date_col]).to_pydatetime())
            helper_ws.write_number(r + 1, base_col_offset + 1, float(trend.iloc[r, conv_col]) * 100)
            helper_ws.write_number(r + 1, base_col_offset + 2, float(trend.iloc[r, error_col]))
            helper_ws.write_number(r + 1, base_col_offset + 3, float(trend.iloc[r, uptime_col]))
        for name, offset, color in [("Conversion %", 1, colors['purple']), ("Error %", 2, colors['red']), ("Uptime %", 3, colors['green'])]:
            chart3.add_series({
                'name': name,
                'categories': ['DashboardData', 1, base_col_offset, trend_rows, base_col_offset],
                'values': ['DashboardData', 1, base_col_offset + offset, trend_rows, base_col_offset + offset],
                'line': {'color': color, 'width': 2.0},
                'marker': {'type': 'circle', 'size': 5, 'border': {'color': color}, 'fill': {'color': color}},
            })
        chart3.set_title({'name': 'Product / Ops / Technical Trend'})
        chart3.set_x_axis({'date_axis': True, 'num_format': 'mmm-yy'})
        chart3.set_y_axis({'name': 'Value'})
        chart3.set_legend({'position': 'bottom'})
        chart3.set_size({'width': 600, 'height': 290})
        ws_dash.insert_chart('A54', chart3)

        alert_rows = len(alert_counts)
        chart4 = workbook.add_chart({'type': 'bar'})
        if alert_rows > 0:
            chart4.add_series({
                'name': 'Alert Count',
                'categories': ['DashboardData', 1, 0, alert_rows, 0],
                'values': ['DashboardData', 1, 1, alert_rows, 1],
                'fill': {'color': colors['orange']},
                'border': {'color': colors['orange']},
                'data_labels': {'value': True},
            })
            chart4.set_title({'name': 'Alert Count by Metric'})
            chart4.set_x_axis({'name': 'Alert Count'})
        else:
            helper_ws.write(0, 12, 'No Alerts')
            helper_ws.write(1, 12, 'No active alerts')
            helper_ws.write(0, 13, 'Count')
            helper_ws.write(1, 13, 0)
            chart4.add_series({
                'name': 'Alert Count',
                'categories': ['DashboardData', 1, 12, 1, 12],
                'values': ['DashboardData', 1, 13, 1, 13],
            })
            chart4.set_title({'name': 'Alert Count by Metric'})
        chart4.set_legend({'none': True})
        chart4.set_size({'width': 600, 'height': 290})
        ws_dash.insert_chart('J54', chart4)


def write_outputs(enriched: pd.DataFrame, summary: pd.DataFrame, status_summary: pd.DataFrame, segment: pd.DataFrame,
                  trend: pd.DataFrame, alerts: pd.DataFrame, insights: list[str], output_dir: Path, source_name: str) -> dict[str, Path]:
    ensure_directory(output_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base = f"kpi_monitoring_{Path(source_name).stem}_{timestamp}"
    enriched_csv = output_dir / f"{base}_enriched.csv"
    summary_csv = output_dir / f"{base}_summary.csv"
    alerts_csv = output_dir / f"{base}_alerts.csv"
    trend_csv = output_dir / f"{base}_monthly_trend.csv"
    segment_csv = output_dir / f"{base}_segment_summary.csv"
    insights_txt = output_dir / f"{base}_insights.txt"
    excel_path = output_dir / f"{base}_dashboard.xlsx"

    enriched.to_csv(enriched_csv, index=False)
    status_summary.to_csv(summary_csv, index=False)
    alerts.to_csv(alerts_csv, index=False)
    trend.to_csv(trend_csv, index=False)
    segment.to_csv(segment_csv, index=False)
    insights_txt.write_text("\n".join(insights), encoding="utf-8")

    write_dashboard_with_native_charts(excel_path, status_summary, alerts, segment, trend, enriched, insights)

    output_map = {
        "enriched_csv": enriched_csv,
        "summary_csv": summary_csv,
        "alerts_csv": alerts_csv,
        "trend_csv": trend_csv,
        "segment_csv": segment_csv,
        "insights_txt": insights_txt,
        "excel_dashboard": excel_path,
    }

    for key, path in list(output_map.items()):
        downloaded = copy_to_downloads(path)
        if downloaded:
            output_map[f"{key}_downloads"] = downloaded
    return output_map


def print_insights(summary: pd.DataFrame, alerts: pd.DataFrame, segment: pd.DataFrame) -> None:
    val = summary.set_index("Metric")["Value"].to_dict()
    print("\n================ KPI MONITORING EXECUTIVE SUMMARY ================")
    print(f"Total Monthly Revenue (k): {val.get('Total Monthly Revenue', 0):,.2f}")
    print(f"Total MRR (k): {val.get('MRR', 0):,.2f}")
    print(f"Average Burn Rate (k): {val.get('Burn Rate', 0):,.2f}")
    print(f"Average CLV/CAC Ratio: {val.get('CLV/CAC Ratio', 0):,.2f}")
    print(f"Weighted Churn Rate: {val.get('Churn Rate', 0):,.2f}%")
    print(f"Weighted NPS: {val.get('NPS', 0):,.2f}")
    print(f"Weighted CSAT: {val.get('CSAT', 0):,.2f}%")
    print(f"Weighted DAU/MAU: {val.get('DAU/MAU', 0):,.2f}")
    print(f"Weighted Conversion Rate: {val.get('Conversion Rate', 0):,.2f}%")
    print(f"Weighted Error Rate: {val.get('Error Rate', 0):,.2f}%")
    print(f"Weighted System Uptime: {val.get('System Uptime', 0):,.2f}%")
    print(f"Average Cycle Time: {val.get('Cycle Time', 0):,.2f} days")

    print("\nTop alert metrics by volume:")
    if alerts.empty:
        print("  No active alerts detected.")
    else:
        top_alerts = alerts.groupby("Metric").size().sort_values(ascending=False).head(5)
        for metric, count in top_alerts.items():
            print(f"  - {metric}: {count} alerts")

    print("\nBest revenue segments:")
    top_segments = segment.nlargest(5, "Revenue")[["StoreLocation", "StoreCategory", "Revenue", "MRR", "AvgNPS", "CLV_CAC_Ratio"]]
    for row in top_segments.itertuples(index=False):
        print(
            f"  - {row.StoreLocation} | {row.StoreCategory}: Revenue={row.Revenue:,.2f}k, "
            f"MRR={row.MRR:,.2f}k, NPS={row.AvgNPS:.1f}, CLV/CAC={row.CLV_CAC_Ratio:.2f}"
        )


def main() -> None:
    args = parse_args()
    source_path = Path(args.source_file)
    output_dir = Path(args.output_dir)

    df = load_source_data(source_path)
    enriched = enrich_dataset(df, months_history=args.months_history)
    thresholds = KPIThresholds()
    summary = build_portfolio_summary(enriched)
    status_summary = build_status_summary(summary, thresholds)
    segment = build_segment_summary(enriched)
    trend = build_monthly_trend(enriched)
    alerts = generate_alerts(enriched, thresholds)
    insights = build_insights(summary, alerts, segment)
    outputs = write_outputs(enriched, summary, status_summary, segment, trend, alerts, insights, output_dir, source_path.name)

    print_insights(summary, alerts, segment)
    print("\nGenerated files:")
    for name, path in outputs.items():
        print(f"  - {name}: {path}")


if __name__ == "__main__":
    main()
