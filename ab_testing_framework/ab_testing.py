
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

st.set_page_config(page_title="A/B Testing Dashboard", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #f7fafc 0%, #eff6ff 100%);
    color: #0f172a;
}
.block-container {
    max-width: 1400px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
[data-testid="stSidebar"] {
    background: #f8fafc;
    border-right: 1px solid rgba(148, 163, 184, 0.25);
}
h1, h2, h3, h4 { color: #0f172a !important; }
.hero {
    background: linear-gradient(135deg, #2563eb 0%, #14b8a6 100%);
    border-radius: 22px;
    padding: 22px 24px;
    color: white;
    box-shadow: 0 14px 32px rgba(37, 99, 235, 0.18);
    margin-bottom: 14px;
}
.hero p, .hero h1 { color: white !important; }
.section-card {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 18px;
    padding: 16px 18px 10px 18px;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
    margin-bottom: 14px;
}
.metric-card {
    background: white;
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    min-height: 108px;
}
.metric-label {
    color: #64748b;
    font-size: 0.9rem;
    margin-bottom: 6px;
}
.metric-value {
    color: #0f172a;
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1.15;
}
.helper {
    color: #64748b;
    font-size: 0.92rem;
}
.recommend-box {
    border-left: 6px solid #2563eb;
    background: #f8fafc;
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 6px;
}
.recommend-box.good { border-left-color: #16a34a; }
.recommend-box.warn { border-left-color: #f59e0b; }
.recommend-box.bad  { border-left-color: #ef4444; }
.legend-chip {
    display: inline-block;
    border-radius: 999px;
    padding: 0.2rem 0.65rem;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 0.35rem;
}
.chip-control { background: rgba(37,99,235,0.12); color: #2563eb; }
.chip-test { background: rgba(20,184,166,0.14); color: #0f766e; }
.chip-sig { background: rgba(22,163,74,0.12); color: #15803d; }
.chip-ns { background: rgba(245,158,11,0.12); color: #b45309; }
.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.85);
    border-radius: 12px;
    padding: 10px 16px;
}
.note-list li { margin-bottom: 0.35rem; }
</style>
""", unsafe_allow_html=True)

RAW_METRICS = ["Spend_USD", "Impressions", "Reach", "Website_Clicks", "Searches", "View_Content", "Add_to_Cart", "Purchase"]
DISPLAY_NAMES = {
    "Spend_USD": "Spend (USD)",
    "Impressions": "Impressions",
    "Reach": "Reach",
    "Website_Clicks": "Website Clicks",
    "Searches": "Searches",
    "View_Content": "View Content",
    "Add_to_Cart": "Add to Cart",
    "Purchase": "Purchases",
    "CTR": "Click-Through Rate",
    "Search_Rate": "Search Rate",
    "View_Rate": "View Content Rate",
    "ATC_Rate": "Add-to-Cart Rate",
    "Purchase_per_Click": "Purchase per Click",
    "Purchase_per_ATC": "Purchase per Add to Cart",
    "Cost_per_Click": "Cost per Click",
    "Cost_per_Purchase": "Cost per Purchase",
}
BETTER_DIRECTION = {
    "Spend_USD": "lower",
    "Impressions": "higher",
    "Reach": "higher",
    "Website_Clicks": "higher",
    "Searches": "higher",
    "View_Content": "higher",
    "Add_to_Cart": "higher",
    "Purchase": "higher",
    "CTR": "higher",
    "Search_Rate": "higher",
    "View_Rate": "higher",
    "ATC_Rate": "higher",
    "Purchase_per_Click": "higher",
    "Purchase_per_ATC": "higher",
    "Cost_per_Click": "lower",
    "Cost_per_Purchase": "lower",
}


def clean_campaign_file(path: str, label: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';')
    df.columns = [
        "Campaign_Name", "Date", "Spend_USD", "Impressions", "Reach", "Website_Clicks",
        "Searches", "View_Content", "Add_to_Cart", "Purchase"
    ]
    df["Date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y", errors="coerce")
    for col in RAW_METRICS:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df["Group"] = label
    return df


@st.cache_data
def load_data():
    control = clean_campaign_file("control_group.csv", "Control")
    test = clean_campaign_file("test_group.csv", "Test")
    for df in (control, test):
        df["CTR"] = np.where(df["Impressions"] > 0, df["Website_Clicks"] / df["Impressions"], np.nan)
        df["Search_Rate"] = np.where(df["Website_Clicks"] > 0, df["Searches"] / df["Website_Clicks"], np.nan)
        df["View_Rate"] = np.where(df["Website_Clicks"] > 0, df["View_Content"] / df["Website_Clicks"], np.nan)
        df["ATC_Rate"] = np.where(df["Website_Clicks"] > 0, df["Add_to_Cart"] / df["Website_Clicks"], np.nan)
        df["Purchase_per_Click"] = np.where(df["Website_Clicks"] > 0, df["Purchase"] / df["Website_Clicks"], np.nan)
        df["Purchase_per_ATC"] = np.where(df["Add_to_Cart"] > 0, df["Purchase"] / df["Add_to_Cart"], np.nan)
        df["Cost_per_Click"] = np.where(df["Website_Clicks"] > 0, df["Spend_USD"] / df["Website_Clicks"], np.nan)
        df["Cost_per_Purchase"] = np.where(df["Purchase"] > 0, df["Spend_USD"] / df["Purchase"], np.nan)
    combined = pd.concat([control, test], ignore_index=True)
    return control, test, combined


def cohens_d(control: pd.Series, test: pd.Series) -> float:
    a = pd.Series(control).dropna()
    b = pd.Series(test).dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan
    va, vb = a.var(ddof=1), b.var(ddof=1)
    pooled = np.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2))
    if pooled == 0 or np.isnan(pooled):
        return np.nan
    return (b.mean() - a.mean()) / pooled


def welch_test(control: pd.Series, test: pd.Series) -> dict:
    a = pd.Series(control).dropna()
    b = pd.Series(test).dropna()
    mean_a, mean_b = a.mean(), b.mean()
    diff = mean_b - mean_a
    out = {
        "n_control": len(a), "n_test": len(b), "mean_control": mean_a, "mean_test": mean_b,
        "diff": diff, "lift_pct": np.nan, "p_value": np.nan, "ci_low": np.nan,
        "ci_high": np.nan, "effect_size": np.nan
    }
    if len(a) < 2 or len(b) < 2:
        return out
    _, p_value = stats.ttest_ind(b, a, equal_var=False, nan_policy='omit')
    va, vb = a.var(ddof=1), b.var(ddof=1)
    se = np.sqrt(va / len(a) + vb / len(b))
    df_num = (va / len(a) + vb / len(b)) ** 2
    df_den = ((va / len(a)) ** 2) / (len(a) - 1) + ((vb / len(b)) ** 2) / (len(b) - 1)
    df_w = df_num / df_den if df_den != 0 else np.nan
    t_crit = stats.t.ppf(0.975, df_w) if pd.notna(df_w) else np.nan
    ci_low = diff - t_crit * se if pd.notna(t_crit) else np.nan
    ci_high = diff + t_crit * se if pd.notna(t_crit) else np.nan
    lift_pct = (diff / mean_a * 100) if mean_a != 0 and pd.notna(mean_a) else np.nan
    out.update({
        "lift_pct": lift_pct,
        "p_value": p_value,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "effect_size": cohens_d(a, b)
    })
    return out


def recommendation_for_metric(metric: str, result: dict, alpha: float) -> dict:
    p = result["p_value"]
    diff = result["diff"]
    direction = BETTER_DIRECTION.get(metric, "higher")
    if pd.isna(p):
        return {
            "title": "Not enough data to test this metric",
            "style": "warn",
            "summary": "At least two valid daily observations are required in both groups.",
        }
    test_better = (diff > 0 and direction == "higher") or (diff < 0 and direction == "lower")
    control_better = (diff < 0 and direction == "higher") or (diff > 0 and direction == "lower")
    if p < alpha and test_better:
        return {
            "title": f"Recommendation: Prefer TEST for {DISPLAY_NAMES[metric]}",
            "style": "good",
            "summary": f"The test campaign outperformed the control campaign with statistical significance (p = {p:.4f}).",
        }
    if p < alpha and control_better:
        return {
            "title": f"Recommendation: Keep CONTROL for {DISPLAY_NAMES[metric]}",
            "style": "bad",
            "summary": f"The control campaign performed better with statistical significance (p = {p:.4f}).",
        }
    return {
        "title": f"Recommendation: No clear winner for {DISPLAY_NAMES[metric]}",
        "style": "warn",
        "summary": f"The result is inconclusive at alpha = {alpha:.2f} (p = {p:.4f}).",
    }


def metric_card(label: str, value: str, delta_text: str = None, color: str = "#0f172a"):
    delta_html = f"<div class='helper' style='margin-top:6px;'>{delta_text}</div>" if delta_text else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color};">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def plot_daily_trend(control_df, test_df, metric):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=control_df["Date"], y=control_df[metric], mode="lines+markers", name="Control", line=dict(color="#2563eb", width=3), marker=dict(size=7)))
    fig.add_trace(go.Scatter(x=test_df["Date"], y=test_df[metric], mode="lines+markers", name="Test", line=dict(color="#14b8a6", width=3), marker=dict(size=7)))
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.75)",
                      height=430, margin=dict(l=30, r=30, t=55, b=30), title=f"Daily {DISPLAY_NAMES[metric]} Trend",
                      xaxis_title="Date", yaxis_title=DISPLAY_NAMES[metric], legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig


def plot_distribution(combined_df, metric):
    fig = px.box(combined_df, x="Group", y=metric, color="Group", points="all", template="plotly_white",
                 color_discrete_map={"Control": "#2563eb", "Test": "#14b8a6"},
                 title=f"Distribution of {DISPLAY_NAMES[metric]} by Group")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.75)",
                      height=430, margin=dict(l=30, r=30, t=55, b=30), xaxis_title="", yaxis_title=DISPLAY_NAMES[metric], showlegend=False)
    return fig


def format_ci(low: float, high: float, metric: str) -> str:
    if pd.isna(low) or pd.isna(high):
        return "N/A"
    fmt = ".4f" if metric not in RAW_METRICS else ",.2f"
    return f"[{format(low, fmt)}, {format(high, fmt)}]"


control_df, test_df, combined_df = load_data()
all_metrics = ["Purchase", "Website_Clicks", "Add_to_Cart", "Reach", "Impressions", "Spend_USD",
               "CTR", "Search_Rate", "View_Rate", "ATC_Rate", "Purchase_per_Click", "Purchase_per_ATC",
               "Cost_per_Click", "Cost_per_Purchase"]

with st.sidebar:
    st.markdown("## Controls")
    selected_metric = st.selectbox("Choose a metric", options=all_metrics, index=0, format_func=lambda x: DISPLAY_NAMES[x])
    alpha = st.select_slider("Significance threshold", options=[0.10, 0.05, 0.01], value=0.05)
    st.markdown("---")
    st.markdown("### Color Legend")
    st.markdown("<span class='legend-chip chip-control'>Control</span><span class='legend-chip chip-test'>Test</span>", unsafe_allow_html=True)
    st.markdown("<span class='legend-chip chip-sig'>Statistically significant</span><span class='legend-chip chip-ns'>Inconclusive</span>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### About the analysis")
    st.markdown("""
- Daily campaign values are compared with Welch's t-test.
- 95% confidence intervals are shown for the mean difference.
- Cohen's d is used as the effect size.
- Lower is better for cost metrics; higher is better for acquisition and conversion metrics.
""")

st.markdown("""
<div class="hero">
    <h1 style="margin-bottom: 0.2rem;">🧪 A/B Testing Dashboard</h1>
    <p style="margin: 0; font-size: 1rem;">
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="section-card">
    <p class="helper" style="margin-bottom: 0.35rem;">
    </p>
</div>
""", unsafe_allow_html=True)

result = welch_test(control_df[selected_metric], test_df[selected_metric])
rec = recommendation_for_metric(selected_metric, result, alpha)

sig_flag = pd.notna(result["p_value"]) and result["p_value"] < alpha
p_color = "#16a34a" if sig_flag else "#b45309"
effect = result["effect_size"]
if pd.isna(effect):
    effect_desc = "N/A"
elif abs(effect) < 0.2:
    effect_desc = f"{effect:.2f} · negligible"
elif abs(effect) < 0.5:
    effect_desc = f"{effect:.2f} · small"
elif abs(effect) < 0.8:
    effect_desc = f"{effect:.2f} · medium"
else:
    effect_desc = f"{effect:.2f} · large"

fmt = ".4f" if selected_metric not in RAW_METRICS else ",.2f"
control_value = format(result["mean_control"], fmt) if pd.notna(result["mean_control"]) else "N/A"
test_value = format(result["mean_test"], fmt) if pd.notna(result["mean_test"]) else "N/A"
diff_value = format(result["diff"], fmt) if pd.notna(result["diff"]) else "N/A"
lift_value = f"{result['lift_pct']:.2f}%" if pd.notna(result["lift_pct"]) else "N/A"
p_value_text = f"{result['p_value']:.4f}" if pd.notna(result["p_value"]) else "N/A"
ci_text = format_ci(result["ci_low"], result["ci_high"], selected_metric)

st.markdown("## Executive Results")
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    metric_card("Control mean", control_value, delta_text=f"n = {result['n_control']}")
with k2:
    metric_card("Test mean", test_value, delta_text=f"n = {result['n_test']}")
with k3:
    if BETTER_DIRECTION[selected_metric] == "higher":
        diff_color = "#14b8a6" if result["diff"] > 0 else "#ef4444"
    else:
        diff_color = "#14b8a6" if result["diff"] < 0 else "#ef4444"
    metric_card("Difference (Test - Control)", diff_value, delta_text=f"Lift = {lift_value}", color=diff_color)
with k4:
    metric_card("p-value", p_value_text, delta_text=f"alpha = {alpha:.2f}", color=p_color)
with k5:
    metric_card("95% confidence interval", ci_text)
with k6:
    metric_card("Effect size (Cohen’s d)", effect_desc)

st.markdown(f"""
<div class="recommend-box {rec['style']}">
    <div style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-bottom:0.35rem;">{rec['title']}</div>
    <div class="helper">{rec['summary']}</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Metric Analysis", "📈 Conversion Funnel", "🧾 Summary Table", "🔎 Raw Data"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.plotly_chart(plot_daily_trend(control_df, test_df, selected_metric), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.plotly_chart(plot_distribution(combined_df, selected_metric), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("How to read the result")
    direction_text = "Lower values are better for this metric." if BETTER_DIRECTION[selected_metric] == "lower" else "Higher values are better for this metric."
    p_text = "Below" if sig_flag else "Above"
    st.markdown(f"""
<ul class='note-list'>
    <li><b>Metric selected:</b> {DISPLAY_NAMES[selected_metric]}</li>
    <li><b>p-value:</b> {p_text} the selected alpha threshold of {alpha:.2f}.</li>
    <li><b>Confidence interval:</b> {ci_text}</li>
    <li><b>Effect size:</b> {effect_desc}</li>
    <li><b>Business rule:</b> {direction_text}</li>
</ul>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Campaign Funnel Overview")
    totals_control = control_df[RAW_METRICS].sum(numeric_only=True)
    totals_test = test_df[RAW_METRICS].sum(numeric_only=True)

    funnel = pd.DataFrame({
        "Stage": ["Impressions", "Clicks", "View Content", "Add to Cart", "Purchases"],
        "Control": [totals_control["Impressions"], totals_control["Website_Clicks"], totals_control["View_Content"], totals_control["Add_to_Cart"], totals_control["Purchase"]],
        "Test": [totals_test["Impressions"], totals_test["Website_Clicks"], totals_test["View_Content"], totals_test["Add_to_Cart"], totals_test["Purchase"]]
    })
    funnel_long = funnel.melt(id_vars="Stage", var_name="Group", value_name="Total")
    fig = px.bar(funnel_long, x="Stage", y="Total", color="Group", barmode="group", template="plotly_white",
                 color_discrete_map={"Control": "#2563eb", "Test": "#14b8a6"}, title="Funnel Totals: Control vs Test")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.75)", height=430,
                      margin=dict(l=30, r=30, t=55, b=30), xaxis_title="", yaxis_title="Total volume")
    st.plotly_chart(fig, use_container_width=True)

    rates = pd.DataFrame({
        "Metric": ["CTR", "Purchase per Click", "Add to Cart per Click", "Cost per Click", "Cost per Purchase"],
        "Control": [
            totals_control["Website_Clicks"] / totals_control["Impressions"],
            totals_control["Purchase"] / totals_control["Website_Clicks"],
            totals_control["Add_to_Cart"] / totals_control["Website_Clicks"],
            totals_control["Spend_USD"] / totals_control["Website_Clicks"],
            totals_control["Spend_USD"] / totals_control["Purchase"],
        ],
        "Test": [
            totals_test["Website_Clicks"] / totals_test["Impressions"],
            totals_test["Purchase"] / totals_test["Website_Clicks"],
            totals_test["Add_to_Cart"] / totals_test["Website_Clicks"],
            totals_test["Spend_USD"] / totals_test["Website_Clicks"],
            totals_test["Spend_USD"] / totals_test["Purchase"],
        ]
    })
    rates["Difference (Test - Control)"] = rates["Test"] - rates["Control"]
    st.dataframe(rates.style.format({"Control": "{:.4f}", "Test": "{:.4f}", "Difference (Test - Control)": "{:.4f}"}), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Summary across all daily metrics")
    summary_rows = []
    for metric in all_metrics:
        r = welch_test(control_df[metric], test_df[metric])
        summary_rows.append({
            "Metric": DISPLAY_NAMES[metric],
            "Control Mean": r["mean_control"],
            "Test Mean": r["mean_test"],
            "Difference (Test - Control)": r["diff"],
            "Lift %": r["lift_pct"],
            "p-value": r["p_value"],
            "CI Low": r["ci_low"],
            "CI High": r["ci_high"],
            "Effect Size (d)": r["effect_size"],
            "Recommendation": recommendation_for_metric(metric, r, alpha)["title"],
        })
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df.style.format({
        "Control Mean": "{:.4f}", "Test Mean": "{:.4f}", "Difference (Test - Control)": "{:.4f}",
        "Lift %": "{:.2f}%", "p-value": "{:.4f}", "CI Low": "{:.4f}", "CI High": "{:.4f}", "Effect Size (d)": "{:.2f}"
    }), use_container_width=True)
    csv = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download A/B Test Summary CSV", data=csv, file_name="ab_test_summary.csv", mime="text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Raw campaign files")
    sub1, sub2 = st.tabs(["Control Campaign", "Test Campaign"])
    with sub1:
        st.dataframe(control_df, use_container_width=True)
    with sub2:
        st.dataframe(test_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="section-card">
    <h3 style="margin-bottom:0.35rem;">About this dashboard</h3>
    <p class="helper">
        This dashboard is designed by Zackery Bradley for end users to pick a metric, review the p-value, confidence interval, effect size,
        and then use the recommendation panel to decide whether the test campaign should be adopted, rejected, or reviewed further.
    </p>
</div>
""", unsafe_allow_html=True)
