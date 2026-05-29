import os
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import certifi
from typing import Dict, Any, List
from streamlit.runtime.scriptrunner import get_script_run_ctx




# -----------------------------------------------------------------------------
# Prevent accidental execution with plain Python
# -----------------------------------------------------------------------------
if get_script_run_ctx() is None:
    raise SystemExit(
        "This file is a Streamlit app.\n\n"
        "Run it with:\n"
        "python -m streamlit run streamlit_usgs_dashboard.py"
    )


# -----------------------------------------------------------------------------
# Streamlit page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="USGS Earthquake Live Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -----------------------------------------------------------------------------
# Feed definitions
# -----------------------------------------------------------------------------
FEEDS = {
    "Past Hour - All": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
    "Past Day - All": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    "Past 7 Days - All": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson",
    "Past 30 Days - All": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson",
    "Past Day - M2.5+": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
    "Past 7 Days - M2.5+": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson",
    "Past 30 Days - M2.5+": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson",
    "Past Day - M4.5+": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson",
    "Past 7 Days - M4.5+": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson",
    "Past 30 Days - M4.5+": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson",
    "Past 30 Days - Significant": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson",
}

SEVERITY_ORDER = ["Minor", "Light", "Moderate", "Strong", "Major", "Great"]


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
def severity_bucket(mag: float) -> str:
    if pd.isna(mag):
        return "Unknown"
    if mag < 2.5:
        return "Minor"
    if mag < 4.5:
        return "Light"
    if mag < 6.0:
        return "Moderate"
    if mag < 7.0:
        return "Strong"
    if mag < 8.0:
        return "Major"
    return "Great"


def safe_region(place: str) -> str:
    if not isinstance(place, str) or not place.strip():
        return "Unknown"
    if " of " in place:
        return place.split(" of ")[-1].strip()
    return place.strip()


def get_ca_bundle_path() -> str:
    """
    Prefer a manually supplied CA bundle if set, otherwise use certifi's bundle.
    This is useful on corporate networks where a custom root certificate may be needed.
    """
    return os.environ.get("REQUESTS_CA_BUNDLE", certifi.where())


@st.cache_data(ttl=300, show_spinner=False)
def fetch_feed(feed_url: str) -> Dict[str, Any]:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Streamlit-USGS-Dashboard/1.0"
    })

    response = session.get(
        feed_url,
        timeout=30,
        verify=get_ca_bundle_path()
    )
    response.raise_for_status()
    return response.json()


def parse_earthquakes(payload: Dict[str, Any], row_cap: int = 9999) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    features = payload.get("features", [])

    for feature in features:
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}
        coords = geom.get("coordinates", [None, None, None])

        rows.append({
            "earthquake_id": feature.get("id"),
            "title": props.get("title"),
            "place": props.get("place"),
            "region": safe_region(props.get("place")),
            "magnitude": props.get("mag"),
            "severity": severity_bucket(props.get("mag")),
            "event_type": props.get("type"),
            "status": props.get("status"),
            "alert": props.get("alert"),
            "tsunami": props.get("tsunami"),
            "significance": props.get("sig"),
            "felt_reports": props.get("felt"),
            "cdi": props.get("cdi"),
            "mmi": props.get("mmi"),
            "mag_type": props.get("magType"),
            "net": props.get("net"),
            "code": props.get("code"),
            "detail_url": props.get("detail"),
            "event_url": props.get("url"),
            "event_time": pd.to_datetime(props.get("time"), unit="ms", utc=True, errors="coerce"),
            "updated_time": pd.to_datetime(props.get("updated"), unit="ms", utc=True, errors="coerce"),
            "longitude": coords[0] if len(coords) > 0 else None,
            "latitude": coords[1] if len(coords) > 1 else None,
            "depth_km": coords[2] if len(coords) > 2 else None,
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.sort_values("event_time", ascending=False).reset_index(drop=True)

    if len(df) > row_cap:
        df = df.head(row_cap).copy()

    df["event_date"] = df["event_time"].dt.date
    df["event_hour"] = df["event_time"].dt.hour
    df["event_day_name"] = df["event_time"].dt.day_name()
    df["event_day_num"] = df["event_time"].dt.dayofweek
    df["days_since_event"] = (
        pd.Timestamp.now(tz="UTC") - df["event_time"]
    ).dt.total_seconds() / 86400.0
    df["updated_lag_minutes"] = (
        df["updated_time"] - df["event_time"]
    ).dt.total_seconds() / 60.0

    return df


def format_delta(curr: int, prev: int) -> str:
    if prev is None:
        return "N/A"
    delta = curr - prev
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta}"


def localize_timestamp(ts: pd.Timestamp) -> str:
    if pd.isna(ts):
        return "N/A"
    return ts.tz_convert("US/Eastern").strftime("%Y-%m-%d %I:%M:%S %p %Z")


def build_download(df: pd.DataFrame) -> bytes:
    export_cols = [
        "earthquake_id", "title", "place", "region", "magnitude", "severity", "event_type",
        "status", "alert", "tsunami", "significance", "felt_reports", "cdi", "mmi", "mag_type",
        "net", "code", "event_time", "updated_time", "longitude", "latitude", "depth_km",
        "detail_url", "event_url"
    ]
    return df[export_cols].to_csv(index=False).encode("utf-8")


def show_empty_state() -> None:
    st.warning("No earthquake records matched the current filter selections.")
    st.stop()


# -----------------------------------------------------------------------------
# App title
# -----------------------------------------------------------------------------
st.title("🌍 USGS Earthquake Live Dashboard")
# st.caption(
#     "Interactive Streamlit dashboard for live USGS earthquake monitoring, "
#     "trend analysis, and lightweight batch/incremental portfolio demos."
# )


# -----------------------------------------------------------------------------
# Sidebar controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Controls")

    selected_feed = st.selectbox("Feed", list(FEEDS.keys()), index=2)
    auto_refresh = st.selectbox("Auto-refresh interval", ["Off", "1 min", "5 min", "15 min"], index=1)
    row_cap = st.slider("Maximum rows to retain", min_value=100, max_value=9999, value=2500, step=100)
    min_mag = st.slider("Minimum magnitude", min_value=0.0, max_value=9.5, value=0.0, step=0.1)
    max_depth = st.slider("Maximum depth (km)", min_value=10, max_value=800, value=800, step=10)
    tsunami_only = st.checkbox("Tsunami-related only")
    alert_filter = st.multiselect("Alert levels", ["green", "yellow", "orange", "red"], default=[])
    severity_filter = st.multiselect("Severity buckets", SEVERITY_ORDER, default=[])
    text_search = st.text_input("Search place/title")
    sort_by = st.selectbox(
        "Sort events by",
        ["Latest event", "Largest magnitude", "Highest significance", "Most recently updated"]
    )

    st.markdown("---")
    st.caption("Tip: use **Past 7 Days** or **M2.5+** feeds to stay lightweight while still showing rich trends.")


# -----------------------------------------------------------------------------
# Optional auto-refresh
# -----------------------------------------------------------------------------
if auto_refresh != "Off":
    seconds = {"1 min": 60, "5 min": 300, "15 min": 900}[auto_refresh]
    st.markdown(f"<meta http-equiv='refresh' content='{seconds}'>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Data retrieval (SAFE VERSION + SSL FIX)
# -----------------------------------------------------------------------------
feed_url = FEEDS[selected_feed]
df = pd.DataFrame()
payload: Dict[str, Any] = {}

try:
    payload = fetch_feed(feed_url)
    df = parse_earthquakes(payload, row_cap=row_cap)

except requests.exceptions.SSLError:
    st.error(
        "SSL certificate verification failed while connecting to the USGS feed.\n\n"
        "This usually happens on a corporate/VPN network where HTTPS traffic is being inspected.\n\n"
        "Try these fixes:\n"
        "1. Run: python -m pip install --upgrade certifi python-certifi-win32\n"
        "2. Restart PyCharm completely\n"
        "3. If your company uses a custom root certificate, set REQUESTS_CA_BUNDLE to that certificate file\n"
    )
    st.stop()

except requests.RequestException as exc:
    st.error(f"Unable to retrieve the live USGS feed. Error: {exc}")
    st.stop()

except Exception as exc:
    st.error(f"Unexpected error while loading the feed: {exc}")
    st.stop()

if df.empty:
    show_empty_state()


# -----------------------------------------------------------------------------
# Metadata
# -----------------------------------------------------------------------------
metadata = payload.get("metadata", {}) or {}
reported_count = metadata.get("count", len(df))
source_generated = (
    pd.to_datetime(metadata.get("generated"), unit="ms", utc=True, errors="coerce")
    if metadata.get("generated")
    else pd.NaT
)


# -----------------------------------------------------------------------------
# Session-state incremental tracking
# -----------------------------------------------------------------------------
if "previous_snapshot" not in st.session_state:
    st.session_state.previous_snapshot = df[["earthquake_id", "updated_time"]].copy()
    new_events = len(df)
    updated_events = 0
else:
    prev_df = st.session_state.previous_snapshot.copy()
    prev_map = {row.earthquake_id: row.updated_time for row in prev_df.itertuples(index=False)}

    current_ids = set(df["earthquake_id"].dropna())
    previous_ids = set(prev_df["earthquake_id"].dropna())

    new_events = len(current_ids - previous_ids)

    updated_events = int(
        sum(
            1
            for row in df[["earthquake_id", "updated_time"]].itertuples(index=False)
            if row.earthquake_id in prev_map
            and pd.notna(row.updated_time)
            and pd.notna(prev_map[row.earthquake_id])
            and row.updated_time > prev_map[row.earthquake_id]
        )
    )

    st.session_state.previous_snapshot = df[["earthquake_id", "updated_time"]].copy()


# -----------------------------------------------------------------------------
# Filters
# -----------------------------------------------------------------------------
filtered = df.copy()
filtered = filtered[filtered["magnitude"].fillna(-999) >= min_mag]
filtered = filtered[filtered["depth_km"].fillna(999999) <= max_depth]

if tsunami_only:
    filtered = filtered[filtered["tsunami"].fillna(0) == 1]

if alert_filter:
    filtered = filtered[filtered["alert"].isin(alert_filter)]

if severity_filter:
    filtered = filtered[filtered["severity"].isin(severity_filter)]

if text_search.strip():
    pattern = text_search.strip().lower()
    filtered = filtered[
        filtered["place"].fillna("").str.lower().str.contains(pattern)
        | filtered["title"].fillna("").str.lower().str.contains(pattern)
        | filtered["region"].fillna("").str.lower().str.contains(pattern)
    ]

sort_map = {
    "Latest event": ["event_time", "magnitude"],
    "Largest magnitude": ["magnitude", "event_time"],
    "Highest significance": ["significance", "event_time"],
    "Most recently updated": ["updated_time", "event_time"],
}
filtered = filtered.sort_values(sort_map[sort_by], ascending=False).reset_index(drop=True)

if filtered.empty:
    show_empty_state()


# -----------------------------------------------------------------------------
# KPI calculations
# -----------------------------------------------------------------------------
latest_event = filtered["event_time"].max()
avg_mag = filtered["magnitude"].mean()
max_mag = filtered["magnitude"].max()
median_depth = filtered["depth_km"].median()
tsunami_count = int(filtered["tsunami"].fillna(0).eq(1).sum())

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Visible Events", f"{len(filtered):,}", delta=format_delta(len(filtered), len(filtered) - new_events))
col2.metric("Average Magnitude", f"{avg_mag:.2f}" if pd.notna(avg_mag) else "N/A")
col3.metric("Max Magnitude", f"{max_mag:.1f}" if pd.notna(max_mag) else "N/A")
col4.metric("Median Depth (km)", f"{median_depth:.1f}" if pd.notna(median_depth) else "N/A")
col5.metric("Tsunami Events", f"{tsunami_count}")
col6.metric("Incremental Changes", f"{new_events} new / {updated_events} updated")


with st.expander("Feed metadata & freshness", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**Selected feed:** {selected_feed}")
    c2.write(f"**Source reported count:** {reported_count:,}")
    c3.write(f"**Source generated:** {localize_timestamp(source_generated)}")
    c4.write(f"**Latest visible quake:** {localize_timestamp(latest_event)}")
    st.write(f"**Feed URL:** {feed_url}")
    st.write(f"**Row cap applied:** {row_cap:,}")
    st.write(f"**CA bundle in use:** {get_ca_bundle_path()}")


# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------
overview_tab, map_tab, trends_tab, pipeline_tab, records_tab = st.tabs([
    "Executive Overview",
    "Map & Events",
    "Trend Analysis",
    "Pipeline Monitoring",
    "Event Records"
])


# -----------------------------------------------------------------------------
# Executive Overview tab
# -----------------------------------------------------------------------------
with overview_tab:
    left, right = st.columns((1.2, 1))

    with left:
        trend = (
            filtered.assign(event_ts=filtered["event_time"].dt.floor("h"))
            .groupby("event_ts", dropna=False)
            .agg(
                event_count=("earthquake_id", "count"),
                avg_magnitude=("magnitude", "mean"),
                max_magnitude=("magnitude", "max")
            )
            .reset_index()
            .sort_values("event_ts")
        )

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=trend["event_ts"],
            y=trend["event_count"],
            name="Event Count"
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend["event_ts"],
            y=trend["avg_magnitude"],
            name="Avg Magnitude",
            yaxis="y2",
            mode="lines+markers"
        ))
        fig_trend.update_layout(
            title="Event Volume Over Time",
            xaxis_title="Timestamp (UTC)",
            yaxis_title="Event Count",
            yaxis2=dict(title="Average Magnitude", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.02, x=0),
            margin=dict(l=10, r=10, t=50, b=10),
            height=420,
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with right:
        counts_by_severity = (
            filtered.groupby("severity", dropna=False)
            .size()
            .reindex(SEVERITY_ORDER, fill_value=0)
            .reset_index(name="count")
        )

        fig_sev = px.bar(
            counts_by_severity,
            x="severity",
            y="count",
            title="Severity Distribution",
            color="severity",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_sev.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=50, b=10),
            height=420
        )
        st.plotly_chart(fig_sev, use_container_width=True)

    left2, right2 = st.columns(2)

    with left2:
        fig_hist = px.histogram(
            filtered,
            x="magnitude",
            nbins=30,
            title="Magnitude Histogram",
            color_discrete_sequence=["#1f77b4"],
        )
        fig_hist.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=380)
        st.plotly_chart(fig_hist, use_container_width=True)

    with right2:
        fig_depth = px.scatter(
            filtered,
            x="depth_km",
            y="magnitude",
            color="severity",
            size="significance",
            hover_name="title",
            title="Depth vs Magnitude",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_depth.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=380)
        st.plotly_chart(fig_depth, use_container_width=True)


# -----------------------------------------------------------------------------
# Map & Events tab
# -----------------------------------------------------------------------------
with map_tab:
    map_left, map_right = st.columns((1.4, 1))

    with map_left:
        map_df = filtered.dropna(subset=["latitude", "longitude"]).copy()

        if map_df.empty:
            st.info("No map-ready records available for the current filters.")
        else:
            fig_map = px.scatter_mapbox(
                map_df,
                lat="latitude",
                lon="longitude",
                size="magnitude",
                color="severity",
                hover_name="title",
                hover_data={
                    "region": True,
                    "depth_km": ":.1f",
                    "magnitude": ":.1f",
                    "event_time": True,
                    "latitude": False,
                    "longitude": False,
                },
                title="Global Earthquake Event Map",
                zoom=0.7,
                height=620,
                mapbox_style="carto-positron",
            )
            fig_map.update_layout(margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig_map, use_container_width=True)

    with map_right:
        top_regions = (
            filtered.groupby("region", dropna=False)
            .agg(
                events=("earthquake_id", "count"),
                avg_mag=("magnitude", "mean"),
                max_mag=("magnitude", "max")
            )
            .reset_index()
            .sort_values(["events", "max_mag"], ascending=False)
            .head(15)
        )

        fig_region = px.bar(
            top_regions.sort_values("events", ascending=True),
            x="events",
            y="region",
            orientation="h",
            title="Top Regions by Event Count",
            hover_data={"avg_mag": ":.2f", "max_mag": ":.1f"},
            color="events",
            color_continuous_scale="Teal",
        )
        fig_region.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=300)
        st.plotly_chart(fig_region, use_container_width=True)

        latest_cols = ["event_time", "magnitude", "depth_km", "region", "title", "event_url"]
        latest_events = filtered.nlargest(10, columns=["event_time"])[latest_cols].copy()
        latest_events["event_time"] = latest_events["event_time"].dt.tz_convert("US/Eastern").dt.strftime(
            "%Y-%m-%d %I:%M %p"
        )

        st.markdown("### Latest 10 Events")
        st.dataframe(
            latest_events.rename(columns={
                "event_time": "Event Time",
                "magnitude": "Magnitude",
                "depth_km": "Depth (km)",
                "region": "Region",
                "title": "Title",
                "event_url": "USGS Link",
            }),
            use_container_width=True,
            hide_index=True,
        )


# -----------------------------------------------------------------------------
# Trend Analysis tab
# -----------------------------------------------------------------------------
with trends_tab:
    t1, t2 = st.columns(2)

    with t1:
        heat = filtered.groupby(["event_day_name", "event_hour"]).size().reset_index(name="count")
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heat["event_day_name"] = pd.Categorical(heat["event_day_name"], categories=day_order, ordered=True)
        heat = heat.sort_values(["event_day_name", "event_hour"])

        pivot = heat.pivot(index="event_day_name", columns="event_hour", values="count").fillna(0)

        fig_heat = px.imshow(
            pivot,
            aspect="auto",
            color_continuous_scale="Blues",
            title="Event Count Heatmap (Day of Week × Hour)"
        )
        fig_heat.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=430)
        st.plotly_chart(fig_heat, use_container_width=True)

    with t2:
        top_sig = filtered.nlargest(15, columns=["significance", "magnitude"])[
            ["title", "magnitude", "significance", "depth_km", "event_time"]
        ].copy()
        top_sig["event_time"] = top_sig["event_time"].dt.tz_convert("US/Eastern").dt.strftime(
            "%Y-%m-%d %I:%M %p"
        )

        st.markdown("### Most Significant Events")
        st.dataframe(top_sig, use_container_width=True, hide_index=True)

    t3, t4 = st.columns(2)

    with t3:
        fig_box = px.box(
            filtered,
            x="severity",
            y="depth_km",
            color="severity",
            category_orders={"severity": SEVERITY_ORDER},
            title="Depth Distribution by Severity",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_box.update_layout(showlegend=False, margin=dict(l=10, r=10, t=50, b=10), height=380)
        st.plotly_chart(fig_box, use_container_width=True)

    with t4:
        event_type_counts = filtered["event_type"].fillna("unknown").value_counts().reset_index()
        event_type_counts.columns = ["event_type", "count"]

        fig_types = px.pie(
            event_type_counts,
            values="count",
            names="event_type",
            title="Event Type Breakdown",
            hole=0.45,
        )
        fig_types.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=380)
        st.plotly_chart(fig_types, use_container_width=True)


# -----------------------------------------------------------------------------
# Pipeline Monitoring tab
# -----------------------------------------------------------------------------
with pipeline_tab:
    p1, p2, p3 = st.columns(3)

    duplicate_ids = int(filtered["earthquake_id"].duplicated().sum())
    null_lat_lon = int(filtered[["latitude", "longitude"]].isna().any(axis=1).sum())
    revised_records = int((filtered["updated_lag_minutes"].fillna(0) > 0).sum())

    p1.metric("Duplicate IDs", duplicate_ids)
    p2.metric("Missing Coordinates", null_lat_lon)
    p3.metric("Revised Records", revised_records)

    c1, c2 = st.columns(2)

    with c1:
        dq = pd.DataFrame({
            "column": filtered.columns,
            "null_count": [int(filtered[col].isna().sum()) for col in filtered.columns],
            "null_pct": [round(float(filtered[col].isna().mean() * 100), 2) for col in filtered.columns],
            "distinct_count": [int(filtered[col].nunique(dropna=True)) for col in filtered.columns],
        }).sort_values(["null_pct", "null_count"], ascending=False)

        st.markdown("### Data Quality Summary")
        st.dataframe(dq, use_container_width=True, hide_index=True, height=420)

    with c2:
        pipeline_info = pd.DataFrame([
            {"Metric": "Source feed", "Value": selected_feed},
            {"Metric": "Feed URL", "Value": feed_url},
            {"Metric": "Source generated", "Value": localize_timestamp(source_generated)},
            {"Metric": "Rows after cap", "Value": f"{len(df):,}"},
            {"Metric": "Rows after filters", "Value": f"{len(filtered):,}"},
            {"Metric": "New events this refresh", "Value": f"{new_events:,}"},
            {"Metric": "Updated events this refresh", "Value": f"{updated_events:,}"},
            {"Metric": "Latest event timestamp", "Value": localize_timestamp(latest_event)},
        ])

        st.markdown("### Incremental Refresh Monitor")
        st.dataframe(pipeline_info, use_container_width=True, hide_index=True, height=420)



# -----------------------------------------------------------------------------
# Event Records tab
# -----------------------------------------------------------------------------
with records_tab:
    r1, r2 = st.columns([1, 1])

    with r1:
        st.download_button(
            label="Download Filtered Events as CSV",
            data=build_download(filtered),
            file_name="usgs_earthquakes_filtered.csv",
            mime="text/csv",
        )

    with r2:
        st.write(f"Showing **{len(filtered):,}** filtered rows (capped from source at **{row_cap:,}**).")

    display_cols = [
        "earthquake_id", "event_time", "updated_time", "magnitude", "severity", "depth_km", "region",
        "place", "alert", "status", "tsunami", "significance", "title", "event_url"
    ]
    display_df = filtered[display_cols].copy()

    display_df["event_time"] = display_df["event_time"].dt.tz_convert("US/Eastern").dt.strftime(
        "%Y-%m-%d %I:%M:%S %p"
    )
    display_df["updated_time"] = display_df["updated_time"].dt.tz_convert("US/Eastern").dt.strftime(
        "%Y-%m-%d %I:%M:%S %p"
    )

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=560)


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("Created by Zackery Bradley to demonstrate live data streaming with End to End development.")
st.caption("""This Streamlit app connects to live USGS earthquake GeoJSON feeds, parses event-level seismic data into a structured Pandas DataFrame, applies interactive user filters, 
and presents the results through KPI metrics, Plotly visualizations, maps, trend analysis, pipeline-monitoring views, and downloadable event records. 
It also includes session-based incremental tracking to simulate new and updated records for a lightweight end-to-end pipeline demonstration.""")