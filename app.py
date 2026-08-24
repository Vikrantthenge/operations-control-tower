import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Vikrant Operations Intelligence Control Tower",
    page_icon="📊",
    layout="wide",
)

st.title("Vikrant Operations Intelligence Control Tower")
st.caption("Operational visibility, exceptions, root-cause signals and action recommendations for high-volume businesses.")

with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload operations CSV", type=["csv"])
    st.markdown("---")
    st.caption("Created by Vikrant Thenge")

def sample_data():
    np.random.seed(7)
    days = pd.date_range("2026-08-01", periods=30, freq="D")
    rows = []
    sites = ["Hub A", "Hub B", "Hub C"]
    vendors = ["Vendor X", "Vendor Y", "Vendor Z"]
    for d in days:
        for site in sites:
            volume = np.random.randint(700, 1400)
            capacity = np.random.randint(850, 1300)
            sla = np.clip(np.random.normal(94, 4), 75, 100)
            backlog = max(0, int(volume - capacity + np.random.randint(-80, 120)))
            overtime = max(0, np.random.normal(22, 10))
            cost = volume * np.random.uniform(52, 68) + overtime * 450
            vendor = np.random.choice(vendors)
            rows.append([d, site, vendor, volume, capacity, sla, backlog, overtime, cost])
    return pd.DataFrame(rows, columns=[
        "date","site","vendor","volume","capacity","sla_pct","backlog","overtime_hours","operating_cost"
    ])

if uploaded:
    df = pd.read_csv(uploaded)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
else:
    df = sample_data()
    st.info("Showing demo data. Upload a CSV using the same template to analyze your own operations.")

required = {"date","site","vendor","volume","capacity","sla_pct","backlog","overtime_hours","operating_cost"}
missing = required - set(df.columns)
if missing:
    st.error(f"Missing required columns: {', '.join(sorted(missing))}")
    st.stop()

df["utilization_pct"] = np.where(df["capacity"] > 0, df["volume"] / df["capacity"] * 100, np.nan)
df["cost_per_unit"] = np.where(df["volume"] > 0, df["operating_cost"] / df["volume"], np.nan)
df["sla_breach"] = df["sla_pct"] < 95
df["capacity_risk"] = df["utilization_pct"] > 100

latest_date = df["date"].max()
latest = df[df["date"] == latest_date].copy()

st.subheader(f"Executive Snapshot · {latest_date.date() if pd.notna(latest_date) else 'Latest'}")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Volume", f"{latest['volume'].sum():,.0f}")
c2.metric("Capacity", f"{latest['capacity'].sum():,.0f}")
c3.metric("Avg SLA", f"{latest['sla_pct'].mean():.1f}%")
c4.metric("Backlog", f"{latest['backlog'].sum():,.0f}")
c5.metric("Cost / Unit", f"₹{latest['cost_per_unit'].mean():,.1f}")

st.markdown("---")
left, right = st.columns([1.25, 1])

with left:
    st.subheader("Performance Trend")
    trend = df.groupby("date", as_index=False).agg(
        volume=("volume","sum"),
        capacity=("capacity","sum"),
        sla_pct=("sla_pct","mean"),
        backlog=("backlog","sum"),
        operating_cost=("operating_cost","sum"),
    )
    st.line_chart(trend.set_index("date")[["volume","capacity"]], height=260)
    st.line_chart(trend.set_index("date")[["sla_pct"]], height=220)

with right:
    st.subheader("Exceptions Requiring Attention")
    exceptions = latest[(latest["sla_breach"]) | (latest["capacity_risk"]) | (latest["backlog"] > 100)].copy()
    if exceptions.empty:
        st.success("No critical exceptions detected in the latest period.")
    else:
        exceptions["priority"] = np.select(
            [
                (exceptions["sla_pct"] < 90) | (exceptions["backlog"] > 250),
                (exceptions["sla_pct"] < 95) | (exceptions["utilization_pct"] > 105),
            ],
            ["Critical","High"],
            default="Medium"
        )
        show = exceptions[["priority","site","vendor","sla_pct","utilization_pct","backlog","overtime_hours"]]
        st.dataframe(show.sort_values(["priority","backlog"], ascending=[True,False]), use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Root-Cause Signals")
rc1, rc2 = st.columns(2)
with rc1:
    site_perf = df.groupby("site", as_index=False).agg(
        avg_sla=("sla_pct","mean"),
        avg_utilization=("utilization_pct","mean"),
        total_backlog=("backlog","sum"),
        avg_cost_per_unit=("cost_per_unit","mean")
    ).sort_values("avg_sla")
    st.write("Site performance")
    st.dataframe(site_perf, use_container_width=True, hide_index=True)

with rc2:
    vendor_perf = df.groupby("vendor", as_index=False).agg(
        avg_sla=("sla_pct","mean"),
        total_backlog=("backlog","sum"),
        avg_cost_per_unit=("cost_per_unit","mean")
    ).sort_values("avg_sla")
    st.write("Vendor performance")
    st.dataframe(vendor_perf, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Recommended Actions")
actions = []
for _, r in latest.iterrows():
    if r["sla_pct"] < 90:
        actions.append(f"**{r['site']}**: SLA is {r['sla_pct']:.1f}%. Run immediate exception review by process stage and vendor.")
    elif r["sla_pct"] < 95:
        actions.append(f"**{r['site']}**: SLA below target at {r['sla_pct']:.1f}%. Check backlog ageing and staffing coverage.")
    if r["utilization_pct"] > 105:
        actions.append(f"**{r['site']}**: Demand is {r['utilization_pct']:.1f}% of capacity. Add temporary capacity or rebalance workload.")
    if r["backlog"] > 200:
        actions.append(f"**{r['site']}**: Backlog at {int(r['backlog'])}. Prioritize oldest/highest-value work and review cut-off rules.")
    if r["overtime_hours"] > 35:
        actions.append(f"**{r['site']}**: Overtime is elevated at {r['overtime_hours']:.1f} hours. Compare roster coverage to hourly demand.")

if actions:
    for a in actions[:10]:
        st.markdown(f"- {a}")
else:
    st.success("No immediate management interventions suggested from the latest data.")

st.markdown("---")
st.subheader("Data Template")
template = pd.DataFrame(columns=sorted(required))
st.download_button(
    "Download CSV template",
    template.to_csv(index=False).encode("utf-8"),
    "vikrant_operations_control_tower_template.csv",
    "text/csv",
)

st.caption("Vikrant Operations Intelligence Control Tower · Created by Vikrant Thenge")
