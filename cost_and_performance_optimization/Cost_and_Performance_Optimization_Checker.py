import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import shutil
import argparse

# ======================================================
# PATH HANDLING (SAFE FOR WINDOWS)
# ======================================================

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def get_output_dir(user_dir=None):
    base = Path(__file__).resolve().parent
    if not user_dir or user_dir == ".":
        out = base / "out"
    else:
        out = Path(user_dir)
        if not out.is_absolute():
            out = base / out
    ensure_dir(out)
    return out

def save_to_downloads(file_path):
    try:
        d = Path.home() / "Downloads"
        ensure_dir(d)
        shutil.copy(file_path, d / file_path.name)
    except:
        pass

# ======================================================
# LOAD DATA
# ======================================================

def load_data(path):
    try:
        df = pd.read_csv(path)
        if "Cost" not in df.columns:
            raise Exception("Bad schema")
        return df
    except:
        print("⚠️ Using synthetic data (input not clean)")
        np.random.seed(42)
        n = 500
        return pd.DataFrame({
            "Date": pd.date_range("2023-01-01", periods=n, freq="H"),
            "Service": np.random.choice(["VM","Storage","Bandwidth","DevOps","DB"], n),
            "Cost": np.random.gamma(2,3,n),
            "CPU": np.random.uniform(10,90,n),
            "Memory": np.random.uniform(20,95,n),
            "Latency": np.random.uniform(50,400,n),
            "Errors": np.random.poisson(2,n),
            "Throughput": np.random.uniform(100,2000,n),
            "PipelineCost": np.random.uniform(0.2,5,n)
        })

# ======================================================
# METRICS ENGINE (YOUR 5 PILLARS)
# ======================================================

def compute_metrics(df):
    df["Idle"] = df["CPU"] < 20

    metrics = {
        "Total Cost": df["Cost"].sum(),
        "Idle Resource %": df["Idle"].mean()*100,
        "Avg CPU": df["CPU"].mean(),
        "Avg Memory": df["Memory"].mean(),

        # Unit econ
        "Cost / Throughput": df["Cost"].sum() / df["Throughput"].sum(),
        "Cost / Pipeline": df["PipelineCost"].mean(),

        # Performance
        "Avg Latency": df["Latency"].mean(),
        "Error Rate": df["Errors"].mean(),
        "Throughput": df["Throughput"].sum(),

        # DevOps
        "Pipeline Cost Total": df["PipelineCost"].sum(),

        # Governance
        "Forecast Proxy": df["Cost"].mean()*24*30
    }

    return pd.DataFrame([metrics])

# ======================================================
# INSIGHTS ENGINE
# ======================================================

def generate_insights(metrics_df, df):
    m = metrics_df.iloc[0]

    insights = []

    if m["Idle Resource %"] > 20:
        insights.append("High idle resources detected → right-size compute or enable auto-scaling.")

    if m["Cost / Throughput"] > 0.01:
        insights.append("Low efficiency: cost per unit of work is high → optimize compute/storage mix.")

    if m["Avg Latency"] < 200:
        insights.append("Strong latency performance → safe opportunity for cost reduction.")

    if m["Error Rate"] < 3:
        insights.append("System stability is good → optimization will likely not degrade performance.")

    if df["Service"].value_counts().idxmax() == "Storage":
        insights.append("Storage is dominant cost → evaluate tier downgrades (Premium → Standard).")

    return insights

# ======================================================
# EXCEL DASHBOARD (NATIVE CHARTS)
# ======================================================

def build_dashboard(outfile, df, metrics_df, insights):

    with pd.ExcelWriter(outfile, engine="xlsxwriter") as writer:

        df.to_excel(writer, sheet_name="Raw Data", index=False)
        metrics_df.to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame({"Insights":insights}).to_excel(writer, sheet_name="Insights", index=False)

        workbook = writer.book
        ws = workbook.add_worksheet("Dashboard")

        # ---- KPI Cards ----
        vals = metrics_df.to_dict("records")[0]

        kpis = [
            ("Total Cost", vals["Total Cost"]),
            ("Idle %", vals["Idle Resource %"]),
            ("Avg CPU", vals["Avg CPU"]),
            ("Latency", vals["Avg Latency"])
        ]

        for i,(k,v) in enumerate(kpis):
            ws.write(i,0,k)
            ws.write(i,1,v)

        # ---- Charts ----
        svc = df.groupby("Service")["Cost"].sum().reset_index()
        svc.to_excel(writer, sheet_name="svc", index=False)

        trend = df.groupby(df["Date"].dt.date)["Cost"].sum().reset_index()
        trend.to_excel(writer, sheet_name="trend", index=False)

        # Chart 1
        chart1 = workbook.add_chart({"type":"column"})
        chart1.add_series({
            "categories": ["svc",1,0,len(svc),0],
            "values": ["svc",1,1,len(svc),1],
        })
        chart1.set_title({"name":"Cost by Service"})
        ws.insert_chart("D2", chart1)

        # Chart 2
        chart2 = workbook.add_chart({"type":"line"})
        chart2.add_series({
            "categories": ["trend",1,0,len(trend),0],
            "values": ["trend",1,1,len(trend),1],
        })
        chart2.set_title({"name":"Cost Trend"})
        ws.insert_chart("D20", chart2)

        # Chart 3
        chart3 = workbook.add_chart({"type":"scatter"})
        chart3.add_series({
            "categories": ["Raw Data",1,3,len(df),3],
            "values": ["Raw Data",1,2,len(df),2],
        })
        chart3.set_title({"name":"CPU vs Cost"})
        ws.insert_chart("D38", chart3)

# ======================================================
# MAIN
# ======================================================

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", default="anonymized_costs_cost_performance_optimization.csv")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()

    output_dir = get_output_dir(args.output_dir)

    df = load_data(args.source_file)

    metrics_df = compute_metrics(df)
    insights = generate_insights(metrics_df, df)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = output_dir / f"cost_dashboard_{ts}.xlsx"

    build_dashboard(outfile, df, metrics_df, insights)

    save_to_downloads(outfile)

    print("\n✅ COMPLETE")
    print("Saved to:", outfile)

# ======================================================

if __name__ == "__main__":
    main()