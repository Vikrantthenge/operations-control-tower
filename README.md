# 🛫 Operations Intelligence Control Tower

**Live demo:** [operations-control.streamlit.app](https://operations-control.streamlit.app/)

A deployment-ready operations analytics dashboard that turns raw operational CSV data into a live control tower — KPI snapshots, SLA/capacity exceptions, site and vendor root-cause signals, cost-per-unit tracking, and prioritized management actions, all updating in real time as you move the threshold sliders.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/streamlit-live-FF4B4B)
![License](https://img.shields.io/badge/status-MVP-brightgreen)

---

## What it does

- **Executive snapshot** — volume, utilisation, SLA, backlog, and cost/unit, with day-over-day deltas
- **Site status board** — every site flagged ON TRACK / AT RISK / CRITICAL against your own thresholds
- **Trends** — demand vs. capacity, backlog build-up, SLA against target, and a day-by-day SLA heatmap
- **Root cause** — SLA and cost by site/vendor, a utilisation-vs-SLA scatter with correlation read-out, and a backlog treemap
- **Actions** — auto-generated, prioritized (Critical/High/Medium) management actions per site and vendor, exportable as CSV
- **Data** — the full filtered dataset with inline progress bars, plus a CSV export

Everything on the board — SLA target, utilisation ceiling, backlog alert, overtime alert — is a live control in the sidebar. Move a slider and the whole dashboard recalculates.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Required CSV columns

| Column            | Description                          |
|-------------------|---------------------------------------|
| `date`            | Date of the record                    |
| `site`            | Site / hub name                       |
| `vendor`          | Vendor name                           |
| `volume`          | Volume handled                        |
| `capacity`        | Available capacity                    |
| `sla_pct`         | SLA achieved, as a percentage         |
| `backlog`         | Open backlog units                    |
| `overtime_hours`  | Overtime hours logged                 |
| `operating_cost`  | Total operating cost                  |

No file? The app falls back to a synthetic 30-day, 3-site demo dataset automatically, so it always runs.

## Demo dataset

A 12,000-row synthetic operations dataset is included as `sample_operations_12000_rows.csv` for realistic testing of KPI, SLA, capacity, exception, and root-cause features.

## Tech stack

- [Streamlit](https://streamlit.io/) for the app framework
- [Plotly](https://plotly.com/python/) for interactive charts
- [pandas](https://pandas.pydata.org/) / [NumPy](https://numpy.org/) for data processing

---

Created by **Vikrant Thenge**

📧 [vikrantthenge@outlook.com](mailto:vikrantthenge@outlook.com) · 💼 [LinkedIn](https://www.linkedin.com/in/vthenge) · 🐙 [GitHub](https://github.com/Vikrantthenge/Apps)
