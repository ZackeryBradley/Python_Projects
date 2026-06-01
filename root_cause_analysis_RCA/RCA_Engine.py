import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

#note: to run, go to the terminal and change the working directory to the folder you created. Then run the file via the terminal
# P1) cd ".\Advanced_Data_Projects\root_cause_analysis_RCA"
# P2) python -m streamlit run RCA_Engine.py

#this app is designed as a template to provide a RCA to a directly ingested ready csv file

# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="RCA Engine Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# Styling
# =========================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #0b1220 0%, #0f172a 100%);
    color: #e5e7eb;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}
[data-testid="stSidebar"] {
    background: #0a0f1c;
    border-right: 1px solid rgba(148, 163, 184, 0.15);
}
h1, h2, h3, h4 {
    color: #f8fafc !important;
}
p, label, div, span {
    color: #cbd5e1;
}
.metric-card {
    background: rgba(15, 23, 42, 0.80);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
}
.section-card {
    background: rgba(15, 23, 42, 0.78);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 20px;
    padding: 18px 20px 10px 20px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
    margin-bottom: 16px;
}
.kpi-label {
    font-size: 0.88rem;
    color: #94a3b8;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: #f8fafc;
}
.helper {
    color: #94a3b8;
    font-size: 0.92rem;
}
.stButton > button {
    background: linear-gradient(90deg, #2563eb 0%, #0ea5e9 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1rem;
    font-weight: 600;
}
.stDownloadButton > button {
    background: linear-gradient(90deg, #16a34a 0%, #14b8a6 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1rem;
    font-weight: 600;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(15, 23, 42, 0.7);
    border-radius: 12px;
    padding: 10px 16px;
    color: #cbd5e1;
}
.stTabs [aria-selected="true"] {
    background: rgba(37, 99, 235, 0.22) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(59, 130, 246, 0.35);
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# Helper Functions
# =========================================================
def safe_pct_change(current, previous):
    if previous == 0:
        return np.nan
    return ((current - previous) / previous) * 100


def prepare_data(df, date_col, kpi_col):
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d[kpi_col] = pd.to_numeric(d[kpi_col], errors="coerce")
    d = d.dropna(subset=[date_col, kpi_col]).copy()
    return d


def get_period_slices(df, date_col, period_days):
    max_date = df[date_col].max()

    current_end = max_date
    current_start = current_end - pd.Timedelta(days=period_days - 1)

    previous_end = current_start - pd.Timedelta(days=1)
    previous_start = previous_end - pd.Timedelta(days=period_days - 1)

    current_df = df[(df[date_col] >= current_start) & (df[date_col] <= current_end)].copy()
    previous_df = df[(df[date_col] >= previous_start) & (df[date_col] <= previous_end)].copy()

    return current_df, previous_df, current_start, current_end, previous_start, previous_end


def calculate_driver_table(current_df, previous_df, dim_col, kpi_col):
    curr = current_df.groupby(dim_col, dropna=False)[kpi_col].sum().reset_index()
    curr.columns = [dim_col, "current_value"]

    prev = previous_df.groupby(dim_col, dropna=False)[kpi_col].sum().reset_index()
    prev.columns = [dim_col, "previous_value"]

    merged = prev.merge(curr, on=dim_col, how="outer").fillna(0)

    merged["delta"] = merged["current_value"] - merged["previous_value"]
    merged["decline_amount"] = merged["previous_value"] - merged["current_value"]
    merged["pct_change"] = np.where(
        merged["previous_value"] != 0,
        (merged["delta"] / merged["previous_value"]) * 100,
        np.nan
    )

    # Only drivers contributing to decline
    total_decline = merged.loc[merged["decline_amount"] > 0, "decline_amount"].sum()
    merged["contribution_pct"] = np.where(
        (merged["decline_amount"] > 0) & (total_decline > 0),
        (merged["decline_amount"] / total_decline) * 100,
        0
    )

    # cross-sectional anomaly detection on delta
    delta_std = merged["delta"].std(ddof=0)
    delta_mean = merged["delta"].mean()

    if delta_std == 0 or np.isnan(delta_std):
        merged["zscore_delta"] = 0
    else:
        merged["zscore_delta"] = (merged["delta"] - delta_mean) / delta_std

    merged["anomaly_flag"] = np.where(
        (merged["delta"] < 0) & (merged["zscore_delta"] <= -1.5),
        "Anomalous Negative Driver",
        ""
    )

    merged["dimension"] = dim_col
    merged["dimension_value"] = merged[dim_col].astype(str)

    cols = [
        "dimension", "dimension_value", "previous_value", "current_value",
        "delta", "decline_amount", "pct_change", "contribution_pct",
        "zscore_delta", "anomaly_flag"
    ]
    return merged[cols].sort_values("decline_amount", ascending=False)


def build_rca_report(driver_df, kpi_name, top_n=5):
    declining = driver_df[driver_df["decline_amount"] > 0].copy()

    if declining.empty:
        return f"No material decline drivers were detected for **{kpi_name}** in the current period versus the prior period."

    top = declining.sort_values("decline_amount", ascending=False).head(top_n)

    lines = []
    for _, row in top.iterrows():
        pct = "N/A" if pd.isna(row["pct_change"]) else f"{row['pct_change']:.1f}%"
        lines.append(
            f"- **{row['dimension']} = {row['dimension_value']}** "
            f"declined by **{row['decline_amount']:,.2f}**, "
            f"contributing **{row['contribution_pct']:.1f}%** of measured decline "
            f"(change: **{pct}**)."
        )

    return "\n".join(lines)


# =========================================================
# Header
# =========================================================
st.markdown("""
<div class="section-card">
    <h1 style="margin-bottom: 0.3rem;">🧠 Root Cause Analysis (RCA) Engine</h1>
    <p class="helper" style="margin-top: 0;">
        Diagnose KPI declines by automatically identifying the dimensions that contributed most to the drop.
    </p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.markdown("## ⚙️ RCA Settings")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    period_days = st.slider(
        "Comparison Window (days)",
        min_value=7,
        max_value=90,
        value=30,
        help="Compares the most recent period to the immediately preceding period."
    )

    top_n = st.slider(
        "Top Drivers to Show",
        min_value=3,
        max_value=15,
        value=8
    )

    run_rca = st.button("Run RCA")

# =========================================================
# Main
# =========================================================
if uploaded_file is None:
    st.markdown("""
    <div class="section-card">
        <h3>How to use this app</h3>
        <ul style="color:#cbd5e1;">
            <li>Upload a dataset with a <b>date column</b>, a <b>KPI column</b>, and business dimensions like region, category, or segment.</li>
            <li>Select the KPI you want to analyze (for example: Sales or Profit).</li>
            <li>Select the dimensions to test as possible decline drivers.</li>
            <li>The app will compare the most recent period to the prior period and produce a <b>Top Drivers of Decline</b> report.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

else:
    df = pd.read_csv(uploaded_file)

    if df.empty:
        st.error("The uploaded file is empty.")
        st.stop()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Dataset Preview")
    st.dataframe(df.head(10), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    columns = df.columns.tolist()

    c1, c2 = st.columns(2)
    with c1:
        date_col = st.selectbox("Select Date Column", columns)
    with c2:
        kpi_col = st.selectbox("Select KPI Column", columns)

    # Suggest dims by excluding chosen fields
    candidate_dims = [c for c in columns if c not in [date_col, kpi_col]]
    selected_dims = st.multiselect(
        "Select Dimensions for RCA",
        candidate_dims,
        default=[c for c in candidate_dims if c in ["Region", "Segment", "Category", "Sub-Category"]][:4]
    )

    if run_rca:
        if not selected_dims:
            st.warning("Please select at least one dimension for RCA.")
            st.stop()

        try:
            analysis_df = prepare_data(df, date_col, kpi_col)

            if analysis_df.empty:
                st.error("No valid rows available after cleaning the selected date and KPI columns.")
                st.stop()

            current_df, previous_df, current_start, current_end, previous_start, previous_end = get_period_slices(
                analysis_df, date_col, period_days
            )

            if current_df.empty or previous_df.empty:
                st.error("Not enough data to compare current and previous periods.")
                st.stop()

            current_total = current_df[kpi_col].sum()
            previous_total = previous_df[kpi_col].sum()
            total_delta = current_total - previous_total
            total_pct = safe_pct_change(current_total, previous_total)

            # Build RCA driver tables
            all_driver_tables = []
            for dim in selected_dims:
                driver_table = calculate_driver_table(current_df, previous_df, dim, kpi_col)
                all_driver_tables.append(driver_table)

            all_drivers = pd.concat(all_driver_tables, ignore_index=True)

            decline_drivers = all_drivers[all_drivers["decline_amount"] > 0].copy()
            top_drivers = decline_drivers.sort_values("decline_amount", ascending=False).head(top_n)

            anomalies = all_drivers[
                (all_drivers["anomaly_flag"] == "Anomalous Negative Driver") &
                (all_drivers["decline_amount"] > 0)
            ].sort_values("decline_amount", ascending=False)

            # =========================================================
            # KPI cards
            # =========================================================
            st.markdown("## KPI Summary")
            k1, k2, k3, k4 = st.columns(4)

            with k1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="kpi-label">Previous Period {kpi_col}</div>
                    <div class="kpi-value">{previous_total:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with k2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="kpi-label">Current Period {kpi_col}</div>
                    <div class="kpi-value">{current_total:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with k3:
                delta_color = "#ef4444" if total_delta < 0 else "#22c55e"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="kpi-label">Absolute Change</div>
                    <div class="kpi-value" style="color:{delta_color};">{total_delta:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with k4:
                pct_display = "N/A" if pd.isna(total_pct) else f"{total_pct:.2f}%"
                pct_color = "#ef4444" if (not pd.isna(total_pct) and total_pct < 0) else "#22c55e"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="kpi-label">Percent Change</div>
                    <div class="kpi-value" style="color:{pct_color};">{pct_display}</div>
                </div>
                """, unsafe_allow_html=True)

            # =========================================================
            # Narrative report
            # =========================================================
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Top Drivers of Decline Report")
            st.markdown(
                f"**Current Period:** {current_start.date()} to {current_end.date()}  \n"
                f"**Previous Period:** {previous_start.date()} to {previous_end.date()}"
            )

            if total_delta < 0:
                st.markdown(
                    f"The selected KPI **{kpi_col}** declined by **{abs(total_delta):,.2f}** "
                    f"(**{abs(total_pct):.2f}%**) versus the prior period."
                    if not pd.isna(total_pct)
                    else f"The selected KPI **{kpi_col}** declined by **{abs(total_delta):,.2f}** versus the prior period."
                )
            else:
                st.markdown(
                    f"The selected KPI **{kpi_col}** did not decline overall in the current period. "
                    f"The RCA tables below still show which dimensions weakened even if the total KPI held up."
                )

            st.markdown(build_rca_report(top_drivers, kpi_col, top_n=top_n))
            st.markdown('</div>', unsafe_allow_html=True)

            # =========================================================
            # Tabs
            # =========================================================
            tab1, tab2, tab3 = st.tabs(["📊 Top Drivers", "🚨 Anomalies", "📄 Detailed RCA"])

            with tab1:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Largest Contributors to Decline")

                if top_drivers.empty:
                    st.info("No decline drivers were found for the selected KPI and period.")
                else:
                    plot_df = top_drivers.copy()
                    plot_df["Driver"] = plot_df["dimension"] + " | " + plot_df["dimension_value"]

                    fig = px.bar(
                        plot_df.sort_values("decline_amount", ascending=True),
                        x="decline_amount",
                        y="Driver",
                        orientation="h",
                        color="dimension",
                        text="decline_amount",
                        template="plotly_dark",
                        title="Top Drivers of KPI Decline"
                    )
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(15, 23, 42, 0.55)",
                        font=dict(color="#e2e8f0"),
                        height=550,
                        xaxis_title="Decline Amount",
                        yaxis_title=""
                    )
                    fig.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(
                        top_drivers[[
                            "dimension", "dimension_value", "previous_value", "current_value",
                            "decline_amount", "pct_change", "contribution_pct"
                        ]],
                        use_container_width=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)

            with tab2:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Anomalous Negative Drivers")

                if anomalies.empty:
                    st.info("No anomalous negative drivers were detected using the current z-score threshold.")
                else:
                    st.dataframe(
                        anomalies[[
                            "dimension", "dimension_value", "previous_value", "current_value",
                            "delta", "decline_amount", "pct_change", "zscore_delta", "anomaly_flag"
                        ]],
                        use_container_width=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)

            with tab3:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Driver Detail by Dimension")

                for dim in selected_dims:
                    st.markdown(f"### {dim}")
                    dim_df = all_drivers[all_drivers["dimension"] == dim].sort_values(
                        "decline_amount", ascending=False
                    )
                    st.dataframe(dim_df, use_container_width=True)

                download_df = all_drivers.copy()
                csv = download_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download RCA Driver Report CSV",
                    data=csv,
                    file_name="rca_driver_report.csv",
                    mime="text/csv"
                )
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("""
            <div class="section-card">
                <h3 style="margin-bottom: 0.4rem;">Project Overview</h3>
                <p class="helper" style="margin-bottom: 0;">
                    This Root Cause Analysis engine was built by Zackery Bradley to compare current and previous performance windows, ranks the
                    dimensions contributing most to KPI decline, and highlights unusually negative movers. It is designed
                    to simulate how analytics teams diagnose business performance drops across regions, customer segments,
                    and product hierarchies.
                </p>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred while running RCA: {e}")