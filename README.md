# Vikrant Operations Intelligence Control Tower

A deployment-ready MVP that converts operational CSV data into:

- KPI visibility
- SLA and capacity exceptions
- Site/vendor root-cause signals
- Cost-per-unit insight
- Management action recommendations

## Preferred public app slug

`vikrant-operations-control-tower`

A likely Streamlit Community Cloud URL, if available, would be:

`https://vikrant-operations-control-tower.streamlit.app`

The exact URL depends on host availability at deployment time.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Required CSV columns

- date
- site
- vendor
- volume
- capacity
- sla_pct
- backlog
- overtime_hours
- operating_cost

Created by **Vikrant Thenge**.


## Demo dataset

A 12,000-row synthetic operations dataset is included as `sample_operations_12000_rows.csv` for realistic testing of KPI, SLA, capacity, exception and forecasting features.
