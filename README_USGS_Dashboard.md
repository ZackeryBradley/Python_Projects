
# USGS Earthquake Live Dashboard

## Files
- `streamlit_usgs_dashboard.py` - main Streamlit dashboard
- `requirements.txt` - Python dependencies

## Run locally
```bash
pip install -r requirements.txt
streamlit run streamlit_usgs_dashboard.py
```

## Features
- Live USGS earthquake feed ingestion
- Interactive filters for feed, magnitude, depth, severity, alert, and search
- KPI cards and executive overview
- Global event map
- Trend analysis and heatmaps
- Pipeline monitoring / data quality tab
- CSV export of filtered events
- Row-cap safeguard (up to 9,999 rows)
