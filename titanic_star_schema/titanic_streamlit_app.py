import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

#note: to run, go to the terminal and change the working directory to the folder you created. Then run the file via the terminal
#P1) cd ".\Advanced_Data_Projects\titanic_star_schema"
#P2) python -m streamlit run titanic_streamlit_app.py

st.set_page_config(
    page_title="Titanic Voyage Intelligence",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILES = {
    "fact": "fact_passenger_outcome.csv",
    "dim_passenger": "dim_passenger.csv",
    "dim_class": "dim_class.csv",
    "dim_embarkation": "dim_embarkation.csv",
    "dim_cabin": "dim_cabin.csv",
    "dim_ticket": "dim_ticket.csv",
    "dim_family": "dim_family.csv",
    "dim_age_range": "dim_age_band.csv",
    "dim_fare_range": "dim_fare_band.csv",
    "dim_source": "dim_source.csv",
}

CHART_HEIGHT = 380
BASE_FONT = 13


def inject_css():
    css_path = Path("style.css")
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True
        )


def chart_theme():
    return {
        "view": {"stroke": None},
        "axis": {
            "labelFontSize": BASE_FONT,
            "titleFontSize": BASE_FONT,
            "labelColor": "#102A43",
            "titleColor": "#102A43",
            "gridColor": "rgba(123,135,148,0.18)",
            "domainColor": "rgba(16,42,67,0.18)",
            "tickColor": "rgba(16,42,67,0.18)",
            "labelLimit": 260,
            "titlePadding": 12,
        },
        "legend": {
            "labelFontSize": BASE_FONT,
            "titleFontSize": BASE_FONT,
            "labelColor": "#102A43",
            "titleColor": "#102A43",
            "symbolType": "circle",
        }
    }


@st.cache_data
def load_star_schema():
    missing = [f for f in DATA_FILES.values() if not Path(f).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required data files: "
            + ", ".join(missing)
            + ". Place the app in the same folder as the star schema CSV files."
        )

    fact = pd.read_csv(DATA_FILES["fact"])
    dim_passenger = pd.read_csv(DATA_FILES["dim_passenger"])
    dim_class = pd.read_csv(DATA_FILES["dim_class"])
    dim_embarkation = pd.read_csv(DATA_FILES["dim_embarkation"])
    dim_cabin = pd.read_csv(DATA_FILES["dim_cabin"])
    dim_ticket = pd.read_csv(DATA_FILES["dim_ticket"])
    dim_family = pd.read_csv(DATA_FILES["dim_family"])
    dim_age_range = pd.read_csv(DATA_FILES["dim_age_range"])
    dim_fare_range = pd.read_csv(DATA_FILES["dim_fare_range"])
    dim_source = pd.read_csv(DATA_FILES["dim_source"])

    if "AgeBand" in dim_age_range.columns:
        dim_age_range = dim_age_range.rename(columns={"AgeBand": "AgeRange"})
    if "FareBand" in dim_fare_range.columns:
        dim_fare_range = dim_fare_range.rename(columns={"FareBand": "FareRange"})

    df = (
        fact.merge(dim_passenger, on="PassengerKey", how="left")
            .merge(dim_class, on="ClassKey", how="left")
            .merge(dim_embarkation, on="EmbarkationKey", how="left")
            .merge(dim_cabin, on="CabinKey", how="left")
            .merge(dim_ticket, on="TicketKey", how="left")
            .merge(dim_family, on="FamilyKey", how="left")
            .merge(dim_age_range, on="AgeBandKey", how="left")
            .merge(dim_fare_range, on="FareBandKey", how="left")
            .merge(dim_source, on="SourceKey", how="left")
    )

    class_order = ["First Class", "Second Class", "Third Class"]
    age_order = [
        "Child (0-12)", "Teen (13-17)", "Young Adult (18-35)",
        "Adult (36-50)", "Mature Adult (51-65)", "Senior (66+)", "Unknown"
    ]
    fare_order = ["Low Fare", "Medium Fare", "High Fare", "Premium Fare", "Unknown"]
    embark_order = ["Cherbourg", "Queenstown", "Southampton", "Unknown"]

    df["ClassName"] = pd.Categorical(df["ClassName"], categories=class_order, ordered=True)
    df["AgeRange"] = pd.Categorical(df["AgeRange"], categories=age_order, ordered=True)
    df["FareRange"] = pd.Categorical(df["FareRange"], categories=fare_order, ordered=True)
    df["EmbarkationName"] = pd.Categorical(df["EmbarkationName"], categories=embark_order, ordered=True)

    df["FareAmount"] = pd.to_numeric(df["FareAmount"], errors="coerce")
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")

    return df


def render_hero_section(total_passengers, survivors, non_survivors, survival_rate, avg_fare, avg_age):
    st.markdown(
        f"""
        <section class='hero-shell'>
            <div class='hero-copy'>
                <div class='eyebrow'>DIMENSIONAL ANALYTICS APP</div>
                <h1 class='hero-title'>Titanic Voyage Intelligence</h1>
            </div>
            <div class='hero-kpi-row'>
                <div class='hero-kpi-card'>
                    <div class='hero-kpi-label'>Passengers</div>
                    <div class='hero-kpi-value'>{total_passengers:,}</div>
                </div>
                <div class='hero-kpi-card'>
                    <div class='hero-kpi-label'>Survivors</div>
                    <div class='hero-kpi-value'>{survivors:,}</div>
                </div>
                <div class='hero-kpi-card'>
                    <div class='hero-kpi-label'>Did Not Survive</div>
                    <div class='hero-kpi-value'>{non_survivors:,}</div>
                </div>
                <div class='hero-kpi-card'>
                    <div class='hero-kpi-label'>Survival Rate</div>
                    <div class='hero-kpi-value'>{survival_rate:.2f}%</div>
                </div>
                <div class='hero-kpi-card'>
                    <div class='hero-kpi-label'>Average Fare</div>
                    <div class='hero-kpi-value'>{('$' + format(avg_fare, ',.2f')) if pd.notna(avg_fare) else 'N/A'}</div>
                </div>
                <div class='hero-kpi-card'>
                    <div class='hero-kpi-label'>Average Age</div>
                    <div class='hero-kpi-value'>{format(avg_age, ',.1f') if pd.notna(avg_age) else 'N/A'}</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def prep_survival_by(data, group_col):
    grp = (
        data.groupby(group_col, dropna=False, observed=False)
        .agg(Passengers=("PassengerCount", "sum"), Survivors=("SurvivedFlag", "sum"))
        .reset_index()
    )
    grp = grp[grp[group_col].notna()]
    grp["Survival Rate %"] = (grp["Survivors"] / grp["Passengers"] * 100).round(2)
    return grp


def render_chart_title(text):
    st.markdown(f"<div class='chart-title'>{text}</div>", unsafe_allow_html=True)


def chart_shell_open():
    return


def chart_shell_close():
    return


def bar_survival_rate(data, group_col, x_title, color="#274C77"):
    grp = prep_survival_by(data, group_col)

    if grp.empty:
        st.info("No data available for this visual with the current filters.")
        return

    max_rate = grp["Survival Rate %"].max()
    y_max = max_rate * 1.18 if pd.notna(max_rate) else 100

    angle = -90 if group_col in ["ClassName", "AgeRange", "FareRange"] else -35

    chart = alt.Chart(grp).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6
    ).encode(
        x=alt.X(
            f"{group_col}:N",
            title=x_title,
            sort=None,
            axis=alt.Axis(
                labelAngle=angle,
                labelAlign="right",
                labelLimit=320
            )
        ),
        y=alt.Y(
            "Survival Rate %:Q",
            title="Survival Rate (%)",
            scale=alt.Scale(domain=[0, y_max])
        ),
        color=alt.value(color),
        tooltip=[
            alt.Tooltip(f"{group_col}:N", title=x_title),
            alt.Tooltip("Passengers:Q", title="Passengers"),
            alt.Tooltip("Survivors:Q", title="Survivors"),
            alt.Tooltip("Survival Rate %:Q", title="Survival Rate (%)")
        ]
    ).properties(height=CHART_HEIGHT)

    text = alt.Chart(grp).mark_text(
        dy=-8,
        color="#102A43"
    ).encode(
        x=alt.X(f"{group_col}:N", sort=None),
        y=alt.Y("Survival Rate %:Q"),
        text=alt.Text("Survival Rate %:Q", format=".2f")
    )

    st.altair_chart((chart + text).configure(**chart_theme()), use_container_width=True)


def stacked_outcome(data, group_col, x_title):
    grp = (
        data.groupby([group_col, "SurvivalStatus"], dropna=False, observed=False)
        .agg(Passenger_Count=("PassengerCount", "sum"))
        .reset_index()
    )
    grp = grp[grp[group_col].notna()]

    if grp.empty:
        st.info("No data available for this visual with the current filters.")
        return

    chart = alt.Chart(grp).mark_bar().encode(
        x=alt.X(
            f"{group_col}:N",
            title=x_title,
            sort=None,
            axis=alt.Axis(
                labelAngle=-25,
                labelAlign="right",
                labelLimit=260
            )
        ),
        y=alt.Y("Passenger_Count:Q", title="Passenger Count"),
        color=alt.Color(
            "SurvivalStatus:N",
            title="Passenger Outcome",
            scale=alt.Scale(
                domain=["Survived", "Did Not Survive"],
                range=["#4F8A8B", "#7B2D26"]
            )
        ),
        tooltip=[
            alt.Tooltip(f"{group_col}:N", title=x_title),
            alt.Tooltip("SurvivalStatus:N", title="Passenger Outcome"),
            alt.Tooltip("Passenger_Count:Q", title="Passenger Count")
        ]
    ).properties(height=CHART_HEIGHT)

    st.altair_chart(chart.configure(**chart_theme()), use_container_width=True)


def sex_age_heatmap(data):
    grp = (
        data.groupby(["Sex", "AgeRange"], dropna=False, observed=False)
        .agg(Passengers=("PassengerCount", "sum"), Survivors=("SurvivedFlag", "sum"))
        .reset_index()
    )

    grp = grp[grp["Sex"].notna() & grp["AgeRange"].notna()]

    if grp.empty:
        st.info("No data available for this visual with the current filters.")
        return

    grp["Survival Rate %"] = (grp["Survivors"] / grp["Passengers"] * 100).round(2)

    chart = alt.Chart(grp).mark_rect().encode(
        x=alt.X(
            "AgeRange:N",
            title="Age Range",
            sort=None,
            axis=alt.Axis(
                labelAngle=-90,
                labelAlign="right",
                labelLimit=320
            )
        ),
        y=alt.Y("Sex:N", title="Sex"),
        color=alt.Color(
            "Survival Rate %:Q",
            title="Survival Rate (%)",
            scale=alt.Scale(
                range=[
                    "#d7ecec",
                    "#9fcfce",
                    "#65b0af",
                    "#2b8d8d",
                    "#0f6f73"
                ]
            )
        ),
        tooltip=[
            alt.Tooltip("Sex:N", title="Sex"),
            alt.Tooltip("AgeRange:N", title="Age Range"),
            alt.Tooltip("Passengers:Q", title="Passengers"),
            alt.Tooltip("Survivors:Q", title="Survivors"),
            alt.Tooltip("Survival Rate %:Q", title="Survival Rate (%)")
        ]
    ).properties(height=CHART_HEIGHT + 30)

    st.altair_chart(chart.configure(**chart_theme()), use_container_width=True)


def profile_mix(data):
    grp = (
        data.groupby(["Sex", "Title"], dropna=False)
        .agg(Passengers=("PassengerCount", "sum"))
        .reset_index()
    )
    grp = grp[grp["Title"].notna()]

    if grp.empty:
        st.info("No data available for this visual with the current filters.")
        return

    chart = alt.Chart(grp).mark_bar().encode(
        x=alt.X("Passengers:Q", title="Passenger Count"),
        y=alt.Y(
            "Title:N",
            title="Passenger Title",
            sort='-x',
            axis=alt.Axis(labelLimit=220)
        ),
        color=alt.Color(
            "Sex:N",
            title="Sex",
            scale=alt.Scale(range=["#274C77", "#6096BA", "#A3CEF1"])
        ),
        tooltip=[
            alt.Tooltip("Sex:N", title="Sex"),
            alt.Tooltip("Title:N", title="Passenger Title"),
            alt.Tooltip("Passengers:Q", title="Passenger Count")
        ]
    ).properties(height=CHART_HEIGHT)

    st.altair_chart(chart.configure(**chart_theme()), use_container_width=True)


def fare_scatter(data):
    clean = data.dropna(subset=["FareAmount", "Age"]).copy()

    if clean.empty:
        st.info("No data available for this visual with the current filters.")
        return

    base = alt.Chart(clean).mark_circle(size=72, opacity=0.68).encode(
        x=alt.X("Age:Q", title="Age"),
        y=alt.Y("FareAmount:Q", title="Fare Amount"),
        color=alt.Color(
            "SurvivalStatus:N",
            title="Passenger Outcome",
            scale=alt.Scale(
                domain=["Survived", "Did Not Survive"],
                range=["#4F8A8B", "#7B2D26"]
            )
        ),
        tooltip=[
            alt.Tooltip("PassengerId:Q", title="Passenger ID"),
            alt.Tooltip("PassengerName:N", title="Passenger Name"),
            alt.Tooltip("Sex:N", title="Sex"),
            alt.Tooltip("Age:Q", title="Age"),
            alt.Tooltip("ClassName:N", title="Passenger Class"),
            alt.Tooltip("FareAmount:Q", title="Fare Amount"),
            alt.Tooltip("SurvivalStatus:N", title="Passenger Outcome")
        ]
    ).properties(height=CHART_HEIGHT)

    st.altair_chart(base.configure(**chart_theme()), use_container_width=True)


def family_line(data):
    grp = (
        data.groupby("FamilySize", dropna=False)
        .agg(Passengers=("PassengerCount", "sum"), Survivors=("SurvivedFlag", "sum"))
        .reset_index()
    )

    if grp.empty:
        st.info("No data available for this visual with the current filters.")
        return

    grp["Survival Rate %"] = (grp["Survivors"] / grp["Passengers"] * 100).round(2)

    chart = alt.Chart(grp).mark_line(
        point=True,
        strokeWidth=3,
        color="#274C77"
    ).encode(
        x=alt.X("FamilySize:O", title="Family Size"),
        y=alt.Y("Survival Rate %:Q", title="Survival Rate (%)"),
        tooltip=[
            alt.Tooltip("FamilySize:O", title="Family Size"),
            alt.Tooltip("Passengers:Q", title="Passengers"),
            alt.Tooltip("Survivors:Q", title="Survivors"),
            alt.Tooltip("Survival Rate %:Q", title="Survival Rate (%)")
        ]
    ).properties(height=CHART_HEIGHT)

    st.altair_chart(chart.configure(**chart_theme()), use_container_width=True)


def filtered_table(data, show=False):
    view_cols = [
        "PassengerId", "PassengerName", "Sex", "Age", "Title", "ClassName",
        "EmbarkationName", "CabinDeck", "TicketPrefix", "FamilySize",
        "AgeRange", "FareRange", "FareAmount", "SurvivalStatus", "SourceDataset"
    ]

    if show:
        st.dataframe(
            data[view_cols].sort_values(["ClassName", "FareAmount"], ascending=[True, False]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Turn on the filter in the sidebar to display row-level passenger records.")

    st.download_button(
        label="Download filtered rows",
        data=data[view_cols].to_csv(index=False).encode("utf-8"),
        file_name="titanic_filtered_export.csv",
        mime="text/csv",
        use_container_width=True
    )


def main():
    inject_css()

    try:
        df = load_star_schema()
    except Exception as e:
        st.error(str(e))
        st.stop()

    df["SurvivalStatus"] = df["SurvivedFlag"].map({1: "Survived", 0: "Did Not Survive"})

    with st.sidebar:
        st.markdown("### Global Filters")
        st.caption("Search within the selectors below to quickly narrow the result set.")

        source = st.multiselect(
            "Source dataset",
            sorted(df["SourceDataset"].dropna().astype(str).unique()),
            default=sorted(df["SourceDataset"].dropna().astype(str).unique()),
            placeholder="Select one or more source datasets"
        )
        classes = st.multiselect(
            "Passenger class",
            [x for x in df["ClassName"].cat.categories.tolist() if x in df["ClassName"].astype(str).unique()],
            default=[x for x in df["ClassName"].cat.categories.tolist() if x in df["ClassName"].astype(str).unique()],
            placeholder="Filter by passenger class"
        )
        sexes = st.multiselect(
            "Sex",
            sorted(df["Sex"].dropna().astype(str).unique()),
            default=sorted(df["Sex"].dropna().astype(str).unique()),
            placeholder="Filter by sex"
        )
        embarked = st.multiselect(
            "Embarkation",
            [x for x in df["EmbarkationName"].cat.categories.tolist() if x in df["EmbarkationName"].astype(str).unique()],
            default=[x for x in df["EmbarkationName"].cat.categories.tolist() if x in df["EmbarkationName"].astype(str).unique()],
            placeholder="Filter by embarkation point"
        )
        age_ranges = st.multiselect(
            "Age range",
            [x for x in df["AgeRange"].cat.categories.tolist() if x in df["AgeRange"].astype(str).unique()],
            default=[x for x in df["AgeRange"].cat.categories.tolist() if x in df["AgeRange"].astype(str).unique()],
            placeholder="Filter by age range"
        )
        fare_ranges = st.multiselect(
            "Fare range",
            [x for x in df["FareRange"].cat.categories.tolist() if x in df["FareRange"].astype(str).unique()],
            default=[x for x in df["FareRange"].cat.categories.tolist() if x in df["FareRange"].astype(str).unique()],
            placeholder="Filter by fare range"
        )
        family_range = st.slider(
            "Family size",
            min_value=int(df["FamilySize"].min()),
            max_value=int(df["FamilySize"].max()),
            value=(int(df["FamilySize"].min()), int(df["FamilySize"].max()))
        )
        show_data = st.toggle("Show row-level explorer", value=False)

    filtered = df[
        df["SourceDataset"].astype(str).isin(source)
        & df["ClassName"].astype(str).isin(classes)
        & df["Sex"].astype(str).isin(sexes)
        & df["EmbarkationName"].astype(str).isin(embarked)
        & df["AgeRange"].astype(str).isin(age_ranges)
        & df["FareRange"].astype(str).isin(fare_ranges)
        & df["FamilySize"].between(family_range[0], family_range[1])
    ].copy()

    total_passengers = int(filtered["PassengerCount"].sum())
    survivors = int(filtered["SurvivedFlag"].sum())
    non_survivors = int(filtered["DiedFlag"].sum())
    survival_rate = (survivors / total_passengers * 100) if total_passengers else 0.0
    avg_fare = filtered["FareAmount"].mean()
    avg_age = filtered["Age"].mean()

    render_hero_section(
        total_passengers,
        survivors,
        non_survivors,
        survival_rate,
        avg_fare,
        avg_age
    )

    overview_tab, segments_tab, fare_tab, explorer_tab = st.tabs(
        ["Overview", "Passenger Segments", "Fare & Family", "Explorer"]
    )

    with overview_tab:
        left, right = st.columns(2, gap="large")
        with left:
            render_chart_title("Survival Rate by Passenger Class")
            bar_survival_rate(filtered, "ClassName", "Passenger Class")
        with right:
            render_chart_title("Passenger Outcomes by Embarkation")
            stacked_outcome(filtered, "EmbarkationName", "Embarkation Point")

        left, right = st.columns(2, gap="large")
        with left:
            render_chart_title("Survival Rate by Age Range")
            bar_survival_rate(filtered, "AgeRange", "Age Range", color="#4F8A8B")
        with right:
            render_chart_title("Survival Rate by Fare Range")
            bar_survival_rate(filtered, "FareRange", "Fare Range", color="#7C9885")

    with segments_tab:
        left, right = st.columns([1.15, 1], gap="large")
        with left:
            render_chart_title("Survival Rate by Age Range and Sex")
            sex_age_heatmap(filtered)
        with right:
            render_chart_title("Passenger Mix by Title")
            profile_mix(filtered)

    with fare_tab:
        left, right = st.columns(2, gap="large")
        with left:
            render_chart_title("Passenger Age vs Fare")
            fare_scatter(filtered)
        with right:
            render_chart_title("Survival Rate by Family Size")
            family_line(filtered)

    with explorer_tab:
        st.subheader("Filtered Passenger Explorer")
        filtered_table(filtered, show=show_data)
    st.caption(
        "This dashboard was developed by Zackery Bradley " 
        "demonstrating dimensional modeling, data transformation, and interactive analytics."
    )
    st.caption(
        "The dashboard is built on a Titanic passenger star schema and provides a passenger-level view "
        "of survival outcomes. It tracks key attributes such as passenger class, embarkation point, "
        "age range, fare range, family size, cabin grouping, and ticket behavior for exploratory analysis."
    )


if __name__ == "__main__":
    main()