from pathlib import Path
import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------
# Page Config
# ---------------------------------
st.set_page_config(
    page_title="Healthcare Data Model Explorer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------
# Theme Constants
# ---------------------------------
PRIMARY_BLUE = "#1C4E80"
SECONDARY_BLUE = "#355C7D"
ACCENT_ORANGE = "#FF6A1A"
ACCENT_ORANGE_LIGHT = "#FF8A3D"
APP_BG = "#cfc9be"
PLOT_BG = "#dfd8cc"
TEXT_MAIN = "#091747"
TEXT_MUTED = "#5f7083"

# ---------------------------------
# Load External CSS
# ---------------------------------
def load_css(file_name="styles.css"):
    css_path = Path(file_name)
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ---------------------------------
# Load Data
# ---------------------------------
@st.cache_data
def load_data(file_source="healthcare_dataset.csv"):
    df = pd.read_csv(file_source)
    df = df.dropna(how="all")
    df.columns = df.columns.str.strip()
    return df

# ---------------------------------
# Cleaning Helpers
# ---------------------------------
def clean_name_value(value):
    if pd.isna(value):
        return pd.NA

    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*,\s*", ", ", value)
    value = value.title()
    value = re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), value)
    value = re.sub(r"\bO'([a-z])", lambda m: "O'" + m.group(1).upper(), value)
    return value


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()

    expected_cols = [
        "Name", "Age", "Gender", "Blood Type", "Medical Condition",
        "Date of Admission", "Doctor", "Hospital", "Insurance Provider", "Billing Amount"
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = pd.NA

    df["Date of Admission"] = pd.to_datetime(df["Date of Admission"], errors="coerce")
    df["Billing Amount"] = pd.to_numeric(df["Billing Amount"], errors="coerce")
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")

    text_cols = [
        "Gender", "Blood Type", "Medical Condition",
        "Doctor", "Hospital", "Insurance Provider"
    ]
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    df["Name"] = df["Name"].astype("string")
    df["Name"] = df["Name"].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    df["Name"] = df["Name"].apply(clean_name_value)

    return df

# ---------------------------------
# Build Star Schema
# ---------------------------------
def build_model(df: pd.DataFrame):
    df = clean_dataframe(df)

    dim_patient = (
        df[["Name", "Age", "Gender", "Blood Type"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_patient["patient_id"] = dim_patient.index + 1
    dim_patient = dim_patient[["patient_id", "Name", "Age", "Gender", "Blood Type"]]

    dim_doctor = df[["Doctor"]].drop_duplicates().reset_index(drop=True)
    dim_doctor["doctor_id"] = dim_doctor.index + 1
    dim_doctor = dim_doctor[["doctor_id", "Doctor"]]

    dim_hospital = df[["Hospital"]].drop_duplicates().reset_index(drop=True)
    dim_hospital["hospital_id"] = dim_hospital.index + 1
    dim_hospital = dim_hospital[["hospital_id", "Hospital"]]

    dim_insurance = df[["Insurance Provider"]].drop_duplicates().reset_index(drop=True)
    dim_insurance["insurance_id"] = dim_insurance.index + 1
    dim_insurance = dim_insurance[["insurance_id", "Insurance Provider"]]

    dim_condition = df[["Medical Condition"]].drop_duplicates().reset_index(drop=True)
    dim_condition["condition_id"] = dim_condition.index + 1
    dim_condition = dim_condition[["condition_id", "Medical Condition"]]

    dim_date = df[["Date of Admission"]].drop_duplicates().reset_index(drop=True)
    dim_date["date_id"] = dim_date.index + 1
    dim_date["year"] = dim_date["Date of Admission"].dt.year
    dim_date["quarter"] = dim_date["Date of Admission"].dt.quarter
    dim_date["month"] = dim_date["Date of Admission"].dt.month
    dim_date["month_name"] = dim_date["Date of Admission"].dt.strftime("%b")
    dim_date["day"] = dim_date["Date of Admission"].dt.day
    dim_date = dim_date[["date_id", "Date of Admission", "year", "quarter", "month", "month_name", "day"]]

    fact = (
        df.merge(dim_patient, on=["Name", "Age", "Gender", "Blood Type"], how="left")
          .merge(dim_doctor, on="Doctor", how="left")
          .merge(dim_hospital, on="Hospital", how="left")
          .merge(dim_insurance, on="Insurance Provider", how="left")
          .merge(dim_condition, on="Medical Condition", how="left")
          .merge(dim_date, on="Date of Admission", how="left")
    )

    fact_table = fact[[
        "patient_id", "doctor_id", "hospital_id", "insurance_id",
        "condition_id", "date_id", "Billing Amount"
    ]].copy()
    fact_table["admission_id"] = range(1, len(fact_table) + 1)
    fact_table = fact_table[[
        "admission_id", "patient_id", "doctor_id", "hospital_id",
        "insurance_id", "condition_id", "date_id", "Billing Amount"
    ]]

    return {
        "raw": df,
        "Dim Patient": dim_patient,
        "Dim Doctor": dim_doctor,
        "Dim Hospital": dim_hospital,
        "Dim Insurance": dim_insurance,
        "Dim Condition": dim_condition,
        "Dim Date": dim_date,
        "Fact Admissions": fact_table,
    }

# ---------------------------------
# Semantic Dataset for Slice & Dice
# ---------------------------------
def create_explorer_dataset(model: dict) -> pd.DataFrame:
    df = model["Fact Admissions"].copy()
    df = df.merge(model["Dim Patient"], on="patient_id", how="left")
    df = df.merge(model["Dim Doctor"], on="doctor_id", how="left")
    df = df.merge(model["Dim Hospital"], on="hospital_id", how="left")
    df = df.merge(model["Dim Insurance"], on="insurance_id", how="left")
    df = df.merge(model["Dim Condition"], on="condition_id", how="left")
    df = df.merge(model["Dim Date"], on="date_id", how="left")
    return df

# ---------------------------------
# Filter Logic
# ---------------------------------
def apply_filters(df: pd.DataFrame):
    st.sidebar.markdown('<div class="sidebar-title">Global Filters</div>', unsafe_allow_html=True)
    st.sidebar.caption("Search within the selectors below to quickly narrow the result set.")

    genders = sorted([x for x in df["Gender"].dropna().unique().tolist()])
    blood_types = sorted([x for x in df["Blood Type"].dropna().unique().tolist()])
    conditions = sorted([x for x in df["Medical Condition"].dropna().unique().tolist()])
    hospitals = sorted([x for x in df["Hospital"].dropna().unique().tolist()])
    doctors = sorted([x for x in df["Doctor"].dropna().unique().tolist()])
    insurance = sorted([x for x in df["Insurance Provider"].dropna().unique().tolist()])

    date_min = df["Date of Admission"].dropna().min()
    date_max = df["Date of Admission"].dropna().max()

    selected_gender = st.sidebar.multiselect("Gender", genders)
    selected_blood = st.sidebar.multiselect("Blood Type", blood_types)
    selected_condition = st.sidebar.multiselect("Medical Condition", conditions)
    selected_hospital = st.sidebar.multiselect("Hospital", hospitals)
    selected_doctor = st.sidebar.multiselect("Doctor", doctors)
    selected_insurance = st.sidebar.multiselect("Insurance Provider", insurance)

    age_min = int(df["Age"].dropna().min()) if df["Age"].dropna().shape[0] else 0
    age_max = int(df["Age"].dropna().max()) if df["Age"].dropna().shape[0] else 100
    selected_age = st.sidebar.slider("Age Range", min_value=age_min, max_value=age_max, value=(age_min, age_max))

    selected_dates = None
    if pd.notna(date_min) and pd.notna(date_max):
        selected_dates = st.sidebar.date_input(
            "Admission Date Range",
            value=(date_min.date(), date_max.date()),
            min_value=date_min.date(),
            max_value=date_max.date(),
        )

    filtered = df.copy()

    if selected_gender:
        filtered = filtered[filtered["Gender"].isin(selected_gender)]
    if selected_blood:
        filtered = filtered[filtered["Blood Type"].isin(selected_blood)]
    if selected_condition:
        filtered = filtered[filtered["Medical Condition"].isin(selected_condition)]
    if selected_hospital:
        filtered = filtered[filtered["Hospital"].isin(selected_hospital)]
    if selected_doctor:
        filtered = filtered[filtered["Doctor"].isin(selected_doctor)]
    if selected_insurance:
        filtered = filtered[filtered["Insurance Provider"].isin(selected_insurance)]

    filtered = filtered[
        (filtered["Age"].fillna(age_min) >= selected_age[0]) &
        (filtered["Age"].fillna(age_max) <= selected_age[1])
    ]

    if selected_dates and len(selected_dates) == 2:
        start_date, end_date = pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1])
        filtered = filtered[
            (filtered["Date of Admission"].dt.normalize() >= start_date.normalize()) &
            (filtered["Date of Admission"].dt.normalize() <= end_date.normalize())
        ]

    active_filters = []
    if selected_gender:
        active_filters.append(f"Gender: {', '.join(selected_gender)}")
    if selected_blood:
        active_filters.append(f"Blood Type: {', '.join(selected_blood)}")
    if selected_condition:
        active_filters.append(f"Condition: {', '.join(selected_condition)}")
    if selected_hospital:
        active_filters.append(f"Hospital: {', '.join(selected_hospital[:3])}{'...' if len(selected_hospital) > 3 else ''}")
    if selected_doctor:
        active_filters.append(f"Doctor: {', '.join(selected_doctor[:3])}{'...' if len(selected_doctor) > 3 else ''}")
    if selected_insurance:
        active_filters.append(f"Insurance: {', '.join(selected_insurance[:3])}{'...' if len(selected_insurance) > 3 else ''}")
    if selected_age != (age_min, age_max):
        active_filters.append(f"Age: {selected_age[0]}-{selected_age[1]}")
    if selected_dates and len(selected_dates) == 2 and pd.notna(date_min) and pd.notna(date_max):
        if selected_dates[0] != date_min.date() or selected_dates[1] != date_max.date():
            active_filters.append(f"Admission Date: {selected_dates[0]} to {selected_dates[1]}")

    return filtered, active_filters

# ---------------------------------
# Display Helpers
# ---------------------------------
def format_table(df: pd.DataFrame):
    display_df = df.copy()
    if "Billing Amount" in display_df.columns:
        display_df["Billing Amount"] = display_df["Billing Amount"].map(
            lambda x: f"${x:,.2f}" if pd.notna(x) else None
        )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def kpi_card_html(title, value, subtitle=""):
    subtitle_html = f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{value}</div>
        {subtitle_html}
    </div>
    """

def render_kpi_cards(cards, cards_per_row=4):
    """
    cards = list of tuples: (title, value, subtitle)
    Renders each card in its own Streamlit column to avoid raw HTML display issues.
    """
    for i in range(0, len(cards), cards_per_row):
        row_cards = cards[i:i + cards_per_row]
        cols = st.columns(len(row_cards))
        for col, (title, value, subtitle) in zip(cols, row_cards):
            with col:
                st.markdown(kpi_card_html(title, value, subtitle), unsafe_allow_html=True)

def style_bar_chart(fig, x_title="", y_title=""):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT_MAIN),
        title_font=dict(color=TEXT_MAIN, size=18),
        xaxis=dict(
            title=x_title,
            tickfont=dict(color="#6b7890"),
            title_font=dict(color="#6b7890"),
            gridcolor="rgba(120,120,120,0.20)"
        ),
        yaxis=dict(
            title=y_title,
            tickfont=dict(color="#6b7890"),
            title_font=dict(color="#6b7890"),
            gridcolor="rgba(120,120,120,0.20)"
        ),
        legend=dict(font=dict(color=TEXT_MAIN))
    )
    return fig

def style_combo_chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT_MAIN),
        title_font=dict(color=TEXT_MAIN, size=18),
        xaxis=dict(title="Admission Month", tickfont=dict(color="#6b7890")),
        yaxis=dict(title="Admissions", tickfont=dict(color="#6b7890")),
        yaxis2=dict(title="Total Billing", overlaying="y", side="right", tickfont=dict(color="#6b7890")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=430
    )
    return fig

# ---------------------------------
# App Header
# ---------------------------------
st.markdown(
    """
    <div class="hero-shell">
        <div class="eyebrow">DIMENSIONAL ANALYTICS APP</div>
        <div class="hero-title">Healthcare Data Model Explorer</div>
        <div class="hero-subtitle">
            Professionally styled Streamlit explorer for star schema modeling,
            interactive slice-and-dice analysis, and business-ready insights.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------
# Data Source
# ---------------------------------
uploaded_file = st.sidebar.file_uploader("Upload a healthcare CSV", type=["csv"])

if uploaded_file is not None:
    raw_df = load_data(uploaded_file)
    dataset_name = uploaded_file.name
else:
    raw_df = load_data("healthcare_dataset.csv")
    dataset_name = "healthcare_dataset.csv"

raw_df = clean_dataframe(raw_df)
model = build_model(raw_df)
explorer_df = create_explorer_dataset(model)
filtered_df, active_filters = apply_filters(explorer_df)

# ---------------------------------
# Dataset Context
# ---------------------------------


# ---------------------------------
# KPI Cards
# ---------------------------------
top_kpi_cards = [
    ("Admissions", f"{len(filtered_df):,}", "Filtered rows"),
    ("Patients", f"{filtered_df['patient_id'].nunique():,}", "Distinct patients"),
    ("Hospitals", f"{filtered_df['hospital_id'].nunique():,}", "Participating facilities"),
    (
        "Total Billing",
        f"${filtered_df['Billing Amount'].sum():,.2f}" if filtered_df["Billing Amount"].notna().any() else "$0.00",
        "Summed billing amount"
    ),
    (
        "Average Billing",
        f"${filtered_df['Billing Amount'].mean():,.2f}" if filtered_df["Billing Amount"].notna().any() else "$0.00",
        "Average per admission"
    ),
    (
        "Average Age",
        f"{filtered_df['Age'].mean():.1f}" if filtered_df["Age"].notna().any() else "0.0",
        "Across filtered patients"
    ),
]
render_kpi_cards(top_kpi_cards, cards_per_row=3)

# ---------------------------------
# Tabs
# ---------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Dashboard",
    "🔍 Slice & Dice Explorer",
    "🧱 Star Schema Tables",
    "✅ Data Quality"
])

with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Executive Billing & Admissions View")

    c1, c2 = st.columns(2)

    with c1:
        condition_summary = (
            filtered_df.groupby("Medical Condition", dropna=False, as_index=False)
            .agg(admissions=("admission_id", "count"))
            .sort_values("admissions", ascending=False)
            .head(10)
        )

        fig1 = px.bar(
            condition_summary,
            x="Medical Condition",
            y="admissions",
            title="Top Conditions by Admissions"
        )
        fig1.update_traces(marker_color=ACCENT_ORANGE)
        fig1 = style_bar_chart(fig1, x_title="Condition", y_title="Admissions")
        fig1.update_layout(height=420)
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        hospital_summary = (
            filtered_df.groupby("Hospital", dropna=False, as_index=False)
            .agg(total_billing=("Billing Amount", "sum"))
            .sort_values("total_billing", ascending=False)
            .head(10)
        )

        fig2 = px.bar(
            hospital_summary,
            x="Hospital",
            y="total_billing",
            title="Top Hospitals by Billing"
        )
        fig2.update_traces(marker_color=ACCENT_ORANGE)
        fig2 = style_bar_chart(fig2, x_title="Hospital", y_title="Total Billing")
        fig2.update_layout(height=420)
        st.plotly_chart(fig2, use_container_width=True)

    trend = (
        filtered_df.dropna(subset=["Date of Admission"])
        .groupby(pd.Grouper(key="Date of Admission", freq="ME"), as_index=False)
        .agg(admissions=("admission_id", "count"), total_billing=("Billing Amount", "sum"))
    )

    if not trend.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=trend["Date of Admission"],
            y=trend["admissions"],
            name="Admissions",
            marker_color=ACCENT_ORANGE
        ))
        fig3.add_trace(go.Scatter(
            x=trend["Date of Admission"],
            y=trend["total_billing"],
            name="Total Billing",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=PRIMARY_BLUE, width=3)
        ))
        fig3 = style_combo_chart(fig3)
        fig3.update_layout(title="Admission Trend with Billing Overlay")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No valid admission dates are available for trend analysis.")

    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Interactive Slice & Dice Analyzer")

    view_cols = [
        "admission_id", "Date of Admission", "Name", "Age", "Gender", "Blood Type",
        "Medical Condition", "Doctor", "Hospital", "Insurance Provider", "Billing Amount"
    ]

    explorer_cols = st.multiselect(
        "Choose columns to display",
        options=view_cols,
        default=view_cols
    )

    summary_dimension = st.selectbox(
        "Summarize by dimension",
        ["Medical Condition", "Hospital", "Doctor", "Insurance Provider", "Gender", "Blood Type", "month_name"]
    )

    metric = st.radio("Metric", ["Admissions", "Total Billing", "Average Billing"], horizontal=True)

    grouped = filtered_df.groupby(summary_dimension, dropna=False, as_index=False).agg(
        Admissions=("admission_id", "count"),
        **{
            "Total Billing": ("Billing Amount", "sum"),
            "Average Billing": ("Billing Amount", "mean")
        }
    )
    grouped = grouped.sort_values(metric, ascending=False)

    fig_dynamic = px.bar(
        grouped.head(15),
        x=summary_dimension,
        y=metric,
        title=f"{metric} by {summary_dimension}"
    )
    fig_dynamic.update_traces(marker_color=ACCENT_ORANGE)
    fig_dynamic = style_bar_chart(fig_dynamic, x_title=summary_dimension, y_title=metric)
    fig_dynamic.update_layout(height=420)
    st.plotly_chart(fig_dynamic, use_container_width=True)

    st.markdown("#### Detailed Record Explorer")
    if explorer_cols:
        display_df = filtered_df[explorer_cols].copy()
        if "Billing Amount" in display_df.columns:
            display_df = display_df.sort_values(by="Billing Amount", ascending=False, na_position="last")
        format_table(display_df)
    else:
        st.warning("Select at least one column to display the detail table.")

    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Star Schema Table Explorer")

    with st.expander("View fact-to-dimension relationships", expanded=False):
        st.markdown(
            """
            **Fact_Admissions** connects to all dimensions using surrogate keys:

            - patient_id → Dim Patient  
            - doctor_id → Dim Doctor  
            - hospital_id → Dim Hospital  
            - insurance_id → Dim Insurance  
            - condition_id → Dim Condition  
            - date_id → Dim Date
            """
        )

    selected_table = st.selectbox(
        "Select modeled table",
        ["Dim Patient", "Dim Doctor", "Dim Hospital", "Dim Insurance", "Dim Condition", "Dim Date", "Fact Admissions"]
    )

    st.caption(f"Rows: {len(model[selected_table]):,} | Columns: {len(model[selected_table].columns)}")
    format_table(model[selected_table])
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Data Quality Checks")

    dq1, dq2 = st.columns(2)

    with dq1:
        missing_by_column = raw_df.isna().sum().reset_index()
        missing_by_column.columns = ["Column", "Missing Values"]

        fig_missing = px.bar(
            missing_by_column,
            x="Column",
            y="Missing Values",
            title="Missing Values by Column"
        )
        fig_missing.update_traces(marker_color=ACCENT_ORANGE)
        fig_missing = style_bar_chart(fig_missing, x_title="Column", y_title="Missing Values")
        fig_missing.update_layout(height=400)
        st.plotly_chart(fig_missing, use_container_width=True)

    with dq2:
        if len(raw_df) > 0:
            completeness = ((1 - (raw_df.isna().sum() / len(raw_df))) * 100).fillna(0).reset_index()
        else:
            completeness = pd.DataFrame({"Column": raw_df.columns, "Completeness %": [0] * len(raw_df.columns)})

        completeness.columns = ["Column", "Completeness %"]

        fig_complete = px.bar(
            completeness,
            x="Column",
            y="Completeness %",
            title="Column Completeness %"
        )
        fig_complete.update_traces(marker_color=PRIMARY_BLUE)
        fig_complete = style_bar_chart(fig_complete, x_title="Column", y_title="Completeness %")
        fig_complete.update_layout(height=400, yaxis_range=[0, 100])
        st.plotly_chart(fig_complete, use_container_width=True)

    st.markdown("#### Duplicate & Type Review")

    review_cards = [
        ("Duplicate Rows", f"{raw_df.duplicated().sum():,}", "Duplicate records"),
        ("Null Admission Dates", f"{raw_df['Date of Admission'].isna().sum():,}", "Missing date values"),
        ("Null Billing Amounts", f"{raw_df['Billing Amount'].isna().sum():,}", "Missing billing values"),
    ]
    render_kpi_cards(review_cards, cards_per_row=3)

    st.markdown("#### Raw Source Preview")
    format_table(raw_df.head(100))
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------
# Footer
# ---------------------------------
st.markdown("---")
st.caption(
    "This dashboard was developed by Zackery Bradley using the healthcare_dataset.csv source dataset, "
    "demonstrating dimensional modeling, data transformation, and interactive analytics."
)
