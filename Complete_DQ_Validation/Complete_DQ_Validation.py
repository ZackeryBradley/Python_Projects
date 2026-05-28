import pandas as pd
import re
import os
from datetime import datetime
import xlsxwriter

# ==========================================
# CONFIG
# ==========================================

INPUT_FILE = "faker_data_dq_checks.csv"

run_ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

SUMMARY_FILE = f"dq_summary_{run_ts}.csv"
FAILURE_FILE = f"dq_failures_{run_ts}.csv"
EXCEL_FILE = f"dq_dashboard_{run_ts}.xlsx"

DOWNLOADS_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
PHONE_REGEX = r"^\+?[0-9\-\.\(\)x\s]{10,}$"
USER_ID_REGEX = r"^\d{3}-\d{2}-\d{4}$"

TODAY = datetime.today()

# ==========================================
# LOAD DATA
# ==========================================

df = pd.read_csv(INPUT_FILE)
df.columns = df.columns.str.strip()

total_rows = len(df)

results = []
failures = []

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def log_result(name, failed, details, severity="MEDIUM"):
    pct = round((failed / total_rows) * 100, 2) if total_rows else 0
    status = "PASS" if failed == 0 else ("WARNING" if pct < 5 else "FAIL")

    results.append({
        "check_name": name,
        "status": status,
        "severity": severity,
        "failed_rows": failed,
        "failure_pct": pct,
        "details": details
    })

def save_file(df_obj, filename):
    df_obj.to_csv(filename, index=False)
    df_obj.to_csv(os.path.join(DOWNLOADS_PATH, filename), index=False)

# ==========================================
# CHECKS
# ==========================================

# Nulls
for col in df.columns:
    log_result(f"null:{col}", df[col].isnull().sum(), "Null values", "HIGH")

# User ID
bad_id = df[~df["user_id"].astype(str).str.match(USER_ID_REGEX, na=False)]
dup_id = df[df.duplicated("user_id", keep=False)]

log_result("user_id_format", len(bad_id), "Bad format", "HIGH")
log_result("user_id_duplicates", len(dup_id), "Duplicates", "HIGH")

failures.append(bad_id.assign(issue="Bad user_id"))
failures.append(dup_id.assign(issue="Duplicate user_id"))

# Email
bad_email = df[~df["email"].astype(str).str.match(EMAIL_REGEX, na=False)]
log_result("email", len(bad_email), "Invalid email", "HIGH")
failures.append(bad_email.assign(issue="Bad email"))

# Phone
bad_phone = df[~df["phone_number"].astype(str).str.match(PHONE_REGEX, na=False)]
log_result("phone", len(bad_phone), "Invalid phone", "HIGH")
failures.append(bad_phone.assign(issue="Bad phone"))

# Dates
df["parsed_date"] = pd.to_datetime(df["date"], errors="coerce")
bad_date = df[df["parsed_date"].isnull()]
future = df[df["parsed_date"] > TODAY]

log_result("date_invalid", len(bad_date), "Invalid date", "HIGH")
log_result("date_future", len(future), "Future dates", "HIGH")

failures.append(bad_date.assign(issue="Bad date"))
failures.append(future.assign(issue="Future date"))

# Duplicates
dup_rows = df[df.duplicated()]
log_result("duplicate_records", len(dup_rows), "Full duplicates", "HIGH")

failures.append(dup_rows.assign(issue="Duplicate record"))

# ==========================================
# CREATE DATAFRAMES
# ==========================================

summary_df = pd.DataFrame(results)
failures_df = pd.concat(failures, ignore_index=True) if failures else pd.DataFrame()

save_file(summary_df, SUMMARY_FILE)
save_file(failures_df, FAILURE_FILE)

# ==========================================
# KPI CALCULATIONS
# ==========================================

def get_pct(check):
    return summary_df.loc[summary_df["check_name"] == check, "failure_pct"].values[0]

email_valid = 100 - get_pct("email")
phone_valid = 100 - get_pct("phone")
dup_pct = get_pct("duplicate_records")

dq_score = round(100 - summary_df["failure_pct"].mean(), 2)

kpi_df = pd.DataFrame({
    "Metric": ["Total Records", "DQ Score", "Valid Emails %", "Valid Phones %", "Duplicate %"],
    "Value": [total_rows, dq_score, email_valid, phone_valid, dup_pct]
})

top_issues_df = summary_df.sort_values("failure_pct", ascending=False).head(5)

# ==========================================
# CREATE EXCEL DASHBOARD
# ==========================================

excel_path = EXCEL_FILE
download_excel_path = os.path.join(DOWNLOADS_PATH, EXCEL_FILE)

with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
    workbook = writer.book

    # Write sheets
    summary_df.to_excel(writer, sheet_name="Summary", index=False)
    failures_df.to_excel(writer, sheet_name="Failures", index=False)
    kpi_df.to_excel(writer, sheet_name="KPI Dashboard", index=False)
    top_issues_df.to_excel(writer, sheet_name="Top Issues", index=False)

    # ======================================
    # KPI DASHBOARD FORMATTING
    # ======================================
    ws = writer.sheets["KPI Dashboard"]

    chart = workbook.add_chart({"type": "column"})

    chart.add_series({
        "categories": "=KPI Dashboard!A2:A6",
        "values": "=KPI Dashboard!B2:B6",
        "data_labels": {"value": True}
    })

    chart.set_title({"name": "Data Quality KPIs"})
    chart.set_x_axis({"name": "Metrics"})
    chart.set_y_axis({"name": "Values"})

    # ✅ Position chart safely (no overlap)
    ws.insert_chart("D2", chart, {'x_offset': 25, 'y_offset': 10})

    # ======================================
    # SUMMARY CHART
    # ======================================
    ws2 = writer.sheets["Summary"]

    chart2 = workbook.add_chart({"type": "bar"})

    chart2.add_series({
        "categories": "=Summary!A2:A20",
        "values": "=Summary!E2:E20",
        "data_labels": {"value": True}
    })

    chart2.set_title({"name": "Failure % by Check"})

    # ✅ Safe positioning — far enough down
    ws2.insert_chart("H2", chart2, {'x_offset': 25, 'y_offset': 10})

# Save to Downloads as well
import shutil
shutil.copy(excel_path, download_excel_path)

# ==========================================
# FINAL PRINT
# ==========================================

print("\n✅ Data Quality Analysis Complete")
print(f"\nExcel Dashboard Created:")
print(f"- {excel_path}")
print(f"- {download_excel_path}")

print("\n📊 Key Insights:")
print(f"- Data Quality Score: {dq_score}%")
print(f"- Valid Emails: {email_valid:.2f}%")
print(f"- Valid Phones: {phone_valid:.2f}%")
print(f"- Duplicate Records: {dup_pct:.2f}%")

print("\n🚨 Top Issues:")
print(top_issues_df[["check_name", "failure_pct"]])