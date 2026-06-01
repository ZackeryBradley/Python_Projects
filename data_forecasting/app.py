import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error

#note: to run, go to the terminal and change the working directory to the folder you created. Then run the file via the terminal
# P1) cd ".\Advanced_Data_Projects\data_forcasting"
# P2) python -m streamlit run app.py

#this app is designed as a template to provide forcasting to a directly ingested forcast ready csv file

# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="Forecasting Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# Custom Dark Theme / CSS
# =========================================================
st.markdown("""
<style>
/* App background */
.stApp {
    background: linear-gradient(180deg, #0b1220 0%, #0f172a 100%);
    color: #e5e7eb;
}

/* Main block */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0a0f1c;
    border-right: 1px solid rgba(148, 163, 184, 0.15);
}

/* Headings */
h1, h2, h3, h4 {
    color: #f8fafc !important;
    letter-spacing: 0.2px;
}

/* Paragraph text */
p, label, div, span {
    color: #cbd5e1;
}

/* Cards */
.metric-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 18px;
    padding: 18px 18px 14px 18px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.28);
}

.section-card {
    background: rgba(15, 23, 42, 0.78);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 20px;
    padding: 18px 20px 10px 20px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
    margin-bottom: 16px;
}

/* KPI label */
.kpi-label {
    font-size: 0.88rem;
    color: #94a3b8;
    margin-bottom: 6px;
}

/* KPI value */
.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #f8fafc;
}

/* Small helper */
.helper {
    color: #94a3b8;
    font-size: 0.9rem;
}

/* Buttons */
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

/* Tabs */
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

/* Dataframe container */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

/* Horizontal rule */
hr {
    border-color: rgba(148, 163, 184, 0.15);
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# Helper Functions
# =========================================================
def safe_mape(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan

    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def prepare_time_series(df, date_col, target_col, freq):
    working = df[[date_col, target_col]].copy()
    working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
    working[target_col] = pd.to_numeric(working[target_col], errors="coerce")

    working = working.dropna().sort_values(date_col)

    if working.empty:
        return pd.DataFrame()

    # Aggregate duplicates by date
    working = working.groupby(date_col, as_index=False)[target_col].sum()

    # Resample to requested frequency
    working = working.set_index(date_col).asfreq(freq)

    # Fill missing values
    working[target_col] = working[target_col].interpolate(method="linear")
    working[target_col] = working[target_col].bfill().ffill()

    working = working.reset_index()
    return working


def build_plotly_layout(title, y_label):
    return dict(
        title=title,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.55)",
        font=dict(color="#e2e8f0"),
        margin=dict(l=30, r=30, t=60, b=30),
        height=500,
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor="rgba(148,163,184,0.10)",
            zeroline=False
        ),
        yaxis=dict(
            title=y_label,
            showgrid=True,
            gridcolor="rgba(148,163,184,0.10)",
            zeroline=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )


def infer_future_index(last_date, periods, freq):
    if freq == "D":
        return pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq="D")
    elif freq == "W":
        return pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=periods, freq="W")
    else:  # Monthly start
        return pd.date_range(start=last_date + pd.offsets.MonthBegin(1), periods=periods, freq="MS")


# =========================================================
# Header
# =========================================================
st.markdown("""
<div class="section-card">
    <h1 style="margin-bottom: 0.3rem;">📈 Forecasting Dashboard</h1>

</div>
""", unsafe_allow_html=True)


# =========================================================
# Sidebar Controls
# =========================================================
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("<p class='helper'>Upload a dataset and configure your time series model settings.</p>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    st.markdown("---")
    st.markdown("### Forecast Settings")

    freq_label = st.selectbox(
        "Time Frequency",
        ["Daily", "Weekly", "Monthly"],
        index=0
    )
    freq_map = {
        "Daily": "D",
        "Weekly": "W",
        "Monthly": "MS"
    }
    freq = freq_map[freq_label]

    test_size = st.slider(
        "Holdout Period",
        min_value=7,
        max_value=180,
        value=30,
        help="Used to evaluate forecast performance on the most recent observations."
    )

    forecast_periods = st.slider(
        "Future Forecast Horizon",
        min_value=7,
        max_value=180,
        value=30
    )

    st.markdown("---")
    st.markdown("### Model Parameters")

    p = st.number_input("AR order (p)", min_value=0, max_value=5, value=1, step=1)
    d = st.number_input("Differencing (d)", min_value=0, max_value=2, value=1, step=1)
    q = st.number_input("MA order (q)", min_value=0, max_value=5, value=1, step=1)

    seasonal_toggle = st.checkbox("Enable Seasonality", value=True)

    if seasonal_toggle:
        P = st.number_input("Seasonal AR (P)", min_value=0, max_value=3, value=1, step=1)
        D = st.number_input("Seasonal Diff (D)", min_value=0, max_value=2, value=1, step=1)
        Q = st.number_input("Seasonal MA (Q)", min_value=0, max_value=3, value=1, step=1)

        default_s = 7 if freq == "D" else 52 if freq == "W" else 12
        s = st.number_input("Seasonal Period (s)", min_value=2, max_value=365, value=default_s, step=1)
    else:
        P, D, Q, s = 0, 0, 0, 0

    run_model = st.button("Run Forecast")


# =========================================================
# Main Logic
# =========================================================
if uploaded_file is None:
    st.markdown("""
    <div class="section-card">
        <h3>Getting Started</h3>
        <p class="helper">
            Upload a CSV file with a date column and a numeric target column.
            Once uploaded, you'll be able to:
        </p>
        <ul style="color:#cbd5e1;">
            <li>Compare a <b>baseline</b> forecast vs <b>SARIMAX</b></li>
            <li>Review <b>RMSE</b> and <b>MAPE</b></li>
            <li>Visualize <b>future forecasts</b> with confidence intervals</li>
            <li>Download the forecast output for reporting or dashboarding</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

else:
    raw_df = pd.read_csv(uploaded_file)

    if raw_df.empty:
        st.error("The uploaded file is empty.")
        st.stop()

    all_columns = raw_df.columns.tolist()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Dataset Preview")
    st.dataframe(raw_df.head(10), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        date_col = st.selectbox("Select Date Column", all_columns)
    with col_b:
        target_col = st.selectbox("Select Target Column", all_columns)

    if run_model:
        try:
            ts_df = prepare_time_series(raw_df, date_col, target_col, freq)

            if ts_df.empty:
                st.error("No valid rows were found after processing the selected columns.")
                st.stop()

            if len(ts_df) <= test_size + 10:
                st.error("Not enough rows for the selected holdout period. Reduce the holdout size or use more data.")
                st.stop()

            train_df = ts_df.iloc[:-test_size].copy()
            test_df = ts_df.iloc[-test_size:].copy()

            y_train = train_df[target_col]
            y_test = test_df[target_col]

            # -----------------------------
            # Baseline forecast
            # -----------------------------
            baseline_pred = y_test.shift(1)
            baseline_pred.iloc[0] = y_train.iloc[-1]

            baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
            baseline_mape = safe_mape(y_test, baseline_pred)

            # -----------------------------
            # SARIMAX forecast
            # -----------------------------
            seasonal_order = (P, D, Q, s) if seasonal_toggle else (0, 0, 0, 0)

            model = SARIMAX(
                y_train,
                order=(p, d, q),
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )

            result = model.fit(disp=False)

            test_forecast_obj = result.get_forecast(steps=test_size)
            sarimax_pred = test_forecast_obj.predicted_mean
            sarimax_ci = test_forecast_obj.conf_int()

            sarimax_rmse = np.sqrt(mean_squared_error(y_test, sarimax_pred))
            sarimax_mape = safe_mape(y_test, sarimax_pred)

            # Refit on full series for future predictions
            full_model = SARIMAX(
                ts_df[target_col],
                order=(p, d, q),
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            ).fit(disp=False)

            future_obj = full_model.get_forecast(steps=forecast_periods)
            future_pred = future_obj.predicted_mean
            future_ci = future_obj.conf_int()

            future_index = infer_future_index(ts_df[date_col].max(), forecast_periods, freq)

            forecast_df = pd.DataFrame({
                "Date": future_index,
                "Forecast": future_pred.values,
                "Lower Bound": future_ci.iloc[:, 0].values,
                "Upper Bound": future_ci.iloc[:, 1].values
            })

            # =========================================================
            # KPI Cards
            # =========================================================
            st.markdown("## Model Summary")

            k1, k2, k3, k4 = st.columns(4)

            with k1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="kpi-label">Baseline RMSE</div>
                    <div class="kpi-value">{baseline_rmse:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with k2:
                baseline_mape_display = "N/A" if np.isnan(baseline_mape) else f"{baseline_mape:.2f}%"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="kpi-label">Baseline MAPE</div>
                    <div class="kpi-value">{baseline_mape_display}</div>
                </div>
                """, unsafe_allow_html=True)

            with k3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="kpi-label">SARIMAX RMSE</div>
                    <div class="kpi-value">{sarimax_rmse:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with k4:
                sarimax_mape_display = "N/A" if np.isnan(sarimax_mape) else f"{sarimax_mape:.2f}%"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="kpi-label">SARIMAX MAPE</div>
                    <div class="kpi-value">{sarimax_mape_display}</div>
                </div>
                """, unsafe_allow_html=True)

            # =========================================================
            # Tabs
            # =========================================================
            tab1, tab2, tab3 = st.tabs(["📊 Performance", "🔮 Future Forecast", "📄 Forecast Output"])

            # -----------------------------
            # Tab 1: Performance
            # -----------------------------
            with tab1:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Baseline vs SARIMAX (Holdout Period)")

                perf_fig = go.Figure()

                perf_fig.add_trace(go.Scatter(
                    x=train_df[date_col],
                    y=train_df[target_col],
                    mode="lines",
                    name="Train Actual",
                    line=dict(color="#38bdf8", width=2)
                ))

                perf_fig.add_trace(go.Scatter(
                    x=test_df[date_col],
                    y=test_df[target_col],
                    mode="lines",
                    name="Test Actual",
                    line=dict(color="#f8fafc", width=2)
                ))

                perf_fig.add_trace(go.Scatter(
                    x=test_df[date_col],
                    y=baseline_pred,
                    mode="lines",
                    name="Baseline Forecast",
                    line=dict(color="#94a3b8", width=2, dash="dash")
                ))

                perf_fig.add_trace(go.Scatter(
                    x=test_df[date_col],
                    y=sarimax_pred,
                    mode="lines",
                    name="SARIMAX Forecast",
                    line=dict(color="#fb923c", width=3)
                ))

                perf_fig.add_trace(go.Scatter(
                    x=test_df[date_col],
                    y=sarimax_ci.iloc[:, 1],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip"
                ))

                perf_fig.add_trace(go.Scatter(
                    x=test_df[date_col],
                    y=sarimax_ci.iloc[:, 0],
                    mode="lines",
                    fill="tonexty",
                    fillcolor="rgba(251, 146, 60, 0.18)",
                    line=dict(width=0),
                    name="Confidence Interval",
                    hoverinfo="skip"
                ))

                perf_fig.update_layout(**build_plotly_layout(
                    "Model Comparison on Holdout Data",
                    target_col
                ))

                st.plotly_chart(perf_fig, use_container_width=True)

                comparison_df = pd.DataFrame({
                    "Model": ["Baseline (Naive)", "SARIMAX"],
                    "RMSE": [baseline_rmse, sarimax_rmse],
                    "MAPE": [baseline_mape, sarimax_mape]
                })

                st.markdown("### Error Metrics")
                st.dataframe(comparison_df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # -----------------------------
            # Tab 2: Future Forecast
            # -----------------------------
            with tab2:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Future Forecast with Confidence Intervals")

                forecast_fig = go.Figure()

                forecast_fig.add_trace(go.Scatter(
                    x=ts_df[date_col],
                    y=ts_df[target_col],
                    mode="lines",
                    name="Historical Actual",
                    line=dict(color="#38bdf8", width=2)
                ))

                forecast_fig.add_trace(go.Scatter(
                    x=forecast_df["Date"],
                    y=forecast_df["Forecast"],
                    mode="lines",
                    name="Future Forecast",
                    line=dict(color="#22c55e", width=3)
                ))

                forecast_fig.add_trace(go.Scatter(
                    x=forecast_df["Date"],
                    y=forecast_df["Upper Bound"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip"
                ))

                forecast_fig.add_trace(go.Scatter(
                    x=forecast_df["Date"],
                    y=forecast_df["Lower Bound"],
                    mode="lines",
                    fill="tonexty",
                    fillcolor="rgba(34, 197, 94, 0.18)",
                    line=dict(width=0),
                    name="Confidence Interval",
                    hoverinfo="skip"
                ))

                forecast_fig.update_layout(**build_plotly_layout(
                    "Forward-Looking Forecast",
                    target_col
                ))

                st.plotly_chart(forecast_fig, use_container_width=True)

                # st.markdown(
                #     "<p class='helper'>This view can be used directly in a portfolio presentation to demonstrate forecasting, uncertainty bands, and model output interpretation.</p>",
                #     unsafe_allow_html=True
                # )
                st.markdown('</div>', unsafe_allow_html=True)

            # -----------------------------
            # Tab 3: Forecast Output
            # -----------------------------
            with tab3:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Forecast Table")
                st.dataframe(forecast_df, use_container_width=True)

                csv_data = forecast_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Forecast CSV",
                    data=csv_data,
                    file_name="forecast_output.csv",
                    mime="text/csv"
                )
                st.markdown('</div>', unsafe_allow_html=True)

            # =========================================================
            # Footer / Portfolio Caption
            # =========================================================
            st.markdown("""
            <div class="section-card" style="margin-top: 8px;">
                <h3 style="margin-bottom: 0.4rem;">Project Overview</h3>
                <p class="helper" style="margin-bottom: 0;">
                    This dashboard was built by Zackery Bradley to demonstrate end-to-end time series forecasting using a baseline benchmark and SARIMAX model.
                    It highlights historical trend analysis, holdout evaluation, confidence intervals, and future forecasting in a
                    business-facing format suitable for portfolio presentation.
                </p>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred while building the forecast: {e}")