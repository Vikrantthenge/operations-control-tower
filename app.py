import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Operations Intelligence Control Tower",
    page_icon="🛫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================
# THEME
# =============================================================
INK = "#0B1220"
SURFACE = "#131C2E"
LINE = "#22304A"
TEXT = "#E6EDF7"
MUTED = "#8CA0BF"

CYAN = "#22D3EE"
LIME = "#A3E635"
AMBER = "#FBBF24"
ROSE = "#FB7185"
VIOLET = "#A78BFA"

SITE_SEQ = [CYAN, VIOLET, LIME, AMBER, ROSE, "#38BDF8", "#F472B6"]
SLA_SCALE = [[0.0, ROSE], [0.5, AMBER], [1.0, LIME]]

PLOTLY_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}

st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp, body, .main {
        background-color: #0B1220;
        color: #E6EDF7;
    }

    .block-container { padding-top: 2.2rem; max-width: 1500px; }

    .board-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px; letter-spacing: .18em; text-transform: uppercase;
        color: #8CA0BF; margin: 0 0 10px 2px;
    }

    /* KPI tiles */
    .kpi {
        background: linear-gradient(160deg, #131C2E 0%, #0E1626 100%);
        border: 1px solid #22304A; border-left: 3px solid var(--accent);
        border-radius: 10px; padding: 14px 16px; height: 116px;
    }
    .kpi-label {
        font-family: 'JetBrains Mono', monospace; font-size: 10.5px;
        letter-spacing: .16em; text-transform: uppercase; color: #8CA0BF;
    }
    .kpi-value {
        font-family: 'JetBrains Mono', monospace; font-weight: 700;
        font-size: 30px; line-height: 1.25; color: #E6EDF7; margin-top: 4px;
    }
    .kpi-delta { font-size: 12px; font-weight: 500; margin-top: 2px; }

    /* Site status board — one row per site */
    .row {
        display: flex; align-items: center; gap: 14px;
        background: #131C2E; border: 1px solid #22304A;
        border-left: 4px solid var(--accent);
        border-radius: 8px; padding: 11px 16px; margin-bottom: 8px;
    }
    .row-site {
        font-family: 'JetBrains Mono', monospace; font-weight: 700;
        font-size: 15px; color: #E6EDF7; min-width: 110px;
    }
    .chip {
        font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700;
        letter-spacing: .12em; padding: 4px 9px; border-radius: 999px;
        background: color-mix(in srgb, var(--accent) 18%, transparent);
        color: var(--accent); border: 1px solid var(--accent); white-space: nowrap;
    }
    .row-metric { font-size: 12.5px; color: #8CA0BF; min-width: 128px; }
    .row-metric b {
        font-family: 'JetBrains Mono', monospace; color: #E6EDF7;
        font-size: 14px; margin-left: 5px;
    }
    .bar-track {
        flex: 1; height: 8px; border-radius: 999px;
        background: #1D2942; overflow: hidden; min-width: 90px;
    }
    .bar-fill { height: 8px; border-radius: 999px; background: var(--accent); }

    div[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)


def style_fig(fig, height=320, legend=True):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=34, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        title=dict(font=dict(size=13, color=MUTED)),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=LINE, font_size=12),
        showlegend=legend,
        legend=dict(orientation="h", y=1.14, x=0, title_text=""),
    )
    fig.update_xaxes(gridcolor=LINE, zeroline=False, linecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zeroline=False, linecolor=LINE)
    return fig


def chart(fig, height=320, legend=True):
    st.plotly_chart(style_fig(fig, height, legend), use_container_width=True, config=PLOTLY_CONFIG)


def kpi(col, label, value, accent, delta=None, delta_suffix="", higher_is_better=True):
    html_delta = "<div class='kpi-delta' style='color:#8CA0BF'>no prior period</div>"
    if delta is not None and np.isfinite(delta):
        good = delta >= 0 if higher_is_better else delta <= 0
        colour = LIME if good else ROSE
        arrow = "▲" if delta >= 0 else "▼"
        html_delta = (
            f"<div class='kpi-delta' style='color:{colour}'>"
            f"{arrow} {abs(delta):,.1f}{delta_suffix} vs prior day</div>"
        )
    col.markdown(
        f"<div class='kpi' style='--accent:{accent}'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>{html_delta}</div>",
        unsafe_allow_html=True,
    )


# =============================================================
# DATA
# =============================================================
REQUIRED = [
    "date", "site", "vendor", "volume", "capacity",
    "sla_pct", "backlog", "overtime_hours", "operating_cost",
]
NUMERIC = ["volume", "capacity", "sla_pct", "backlog", "overtime_hours", "operating_cost"]


@st.cache_data
def sample_data():
    rng = np.random.default_rng(7)
    days = pd.date_range("2026-08-01", periods=30, freq="D")
    sites = ["Hub A", "Hub B", "Hub C"]
    vendors = ["Vendor X", "Vendor Y", "Vendor Z"]
    # Each site has its own character so the root-cause views show real signal.
    profile = {
        "Hub A": dict(vol=1250, cap=1300, sla=96.5),
        "Hub B": dict(vol=1050, cap=1000, sla=92.0),
        "Hub C": dict(vol=820, cap=980, sla=95.0),
    }
    rows = []
    for i, d in enumerate(days):
        weekend = d.weekday() >= 5
        for site in sites:
            p = profile[site]
            volume = int(p["vol"] * (0.85 if weekend else 1.0) * rng.normal(1, 0.09))
            capacity = int(p["cap"] * (0.8 if weekend else 1.0))
            strain = max(0.0, volume / max(capacity, 1) - 1)
            sla = float(np.clip(rng.normal(p["sla"], 2.0) - strain * 22, 70, 100))
            backlog = max(0, int(volume - capacity + rng.normal(0, 60)))
            overtime = float(max(0, rng.normal(18, 7) + strain * 60))
            cost = volume * rng.uniform(52, 66) + overtime * 450
            rows.append([
                d, site, vendors[(i + sites.index(site)) % 3],
                volume, capacity, sla, backlog, overtime, cost,
            ])
    return pd.DataFrame(rows, columns=REQUIRED)


with st.sidebar:
    st.markdown("<p class='board-title'>Data source</p>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload operations CSV", type=["csv"], label_visibility="collapsed")

if uploaded:
    df = pd.read_csv(uploaded)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        st.error(
            "This file is missing these columns: " + ", ".join(missing)
            + ". Download the template below the tabs and match the headers."
        )
        st.stop()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    dropped = int(df["date"].isna().sum())
    df = df.dropna(subset=["date"]).copy()
    if df.empty:
        st.error("No usable rows after reading the file. Check that the date column parses.")
        st.stop()
    if dropped:
        st.warning(f"Skipped {dropped} row(s) with an unreadable date.")
else:
    df = sample_data()

# =============================================================
# FILTERS
# =============================================================
dmin, dmax = df["date"].min().date(), df["date"].max().date()
all_sites = sorted(df["site"].dropna().unique().tolist())
all_vendors = sorted(df["vendor"].dropna().unique().tolist())

with st.sidebar:
    st.markdown("<p class='board-title'>Filters</p>", unsafe_allow_html=True)
    if dmin == dmax:
        start, end = dmin, dmax
        st.caption(f"Single day of data: {dmin}")
    else:
        start, end = st.slider(
            "Date range", min_value=dmin, max_value=dmax, value=(dmin, dmax), format="DD MMM"
        )
    sites = st.multiselect("Sites", all_sites, default=all_sites)
    vendors = st.multiselect("Vendors", all_vendors, default=all_vendors)

    st.markdown("<p class='board-title'>Thresholds</p>", unsafe_allow_html=True)
    sla_target = st.slider("SLA target %", 80.0, 99.5, 95.0, 0.5)
    util_limit = st.slider("Utilisation ceiling %", 90, 130, 100, 1)
    backlog_limit = st.slider("Backlog alert", 0, 800, 100, 25)
    overtime_limit = st.slider("Overtime alert (hours)", 0, 120, 35, 5)

    st.markdown("<p class='board-title'>Template</p>", unsafe_allow_html=True)
    st.download_button(
        "Download CSV template",
        data=pd.DataFrame(columns=REQUIRED).to_csv(index=False).encode("utf-8"),
        file_name="operations_control_tower_template.csv",
        mime="text/csv",
        use_container_width=True,
    )

mask = (
    (df["date"].dt.date >= start)
    & (df["date"].dt.date <= end)
    & (df["site"].isin(sites))
    & (df["vendor"].isin(vendors))
)
f = df.loc[mask].copy()

st.title("Operations Intelligence Control Tower")
st.caption(
    "Live visibility, exceptions, root-cause signals and recommended actions "
    "for high-volume operations. Every threshold on the left is live — move it "
    "and the whole board recalculates."
)

if f.empty:
    st.warning("Nothing matches these filters. Widen the date range or add a site back.")
    st.stop()

# =============================================================
# DERIVED METRICS
# =============================================================
f["utilization_pct"] = np.where(f["capacity"] > 0, f["volume"] / f["capacity"] * 100, np.nan)
f["cost_per_unit"] = np.where(f["volume"] > 0, f["operating_cost"] / f["volume"], np.nan)
f["sla_breach"] = f["sla_pct"] < sla_target
f["capacity_risk"] = f["utilization_pct"] > util_limit

dates = sorted(f["date"].unique())
as_of = dates[-1]
prior = dates[-2] if len(dates) > 1 else None

cur = f[f["date"] == as_of]
prv = f[f["date"] == prior] if prior is not None else None


def period(frame):
    if frame is None or frame.empty:
        return None
    vol = frame["volume"].sum()
    cap = frame["capacity"].sum()
    return dict(
        volume=vol,
        capacity=cap,
        sla=frame["sla_pct"].mean(),
        backlog=frame["backlog"].sum(),
        cpu=frame["operating_cost"].sum() / vol if vol else np.nan,
        util=vol / cap * 100 if cap else np.nan,
        overtime=frame["overtime_hours"].sum(),
    )


now, was = period(cur), period(prv)


def d(key):
    if was is None or not np.isfinite(was[key]):
        return None
    return now[key] - was[key]


st.markdown(
    f"<p class='board-title'>Snapshot · {pd.Timestamp(as_of).strftime('%d %b %Y')} · "
    f"{len(sites)} site(s) · target {sla_target:.1f}%</p>",
    unsafe_allow_html=True,
)

k = st.columns(5)
kpi(k[0], "Volume", f"{now['volume']:,.0f}", CYAN, d("volume"))
kpi(k[1], "Utilisation", f"{now['util']:.1f}%", VIOLET, d("util"), "pp", higher_is_better=False)
kpi(k[2], "Avg SLA", f"{now['sla']:.1f}%", LIME if now["sla"] >= sla_target else ROSE,
    d("sla"), "pp")
kpi(k[3], "Backlog", f"{now['backlog']:,.0f}", AMBER, d("backlog"), higher_is_better=False)
kpi(k[4], "Cost / unit", f"₹{now['cpu']:,.1f}", ROSE, d("cpu"), higher_is_better=False)

# =============================================================
# SITE STATUS BOARD
# =============================================================
st.markdown("<p class='board-title' style='margin-top:22px'>Site status</p>", unsafe_allow_html=True)

board = (
    cur.groupby("site", as_index=False)
    .agg(
        volume=("volume", "sum"),
        capacity=("capacity", "sum"),
        sla_pct=("sla_pct", "mean"),
        backlog=("backlog", "sum"),
        overtime_hours=("overtime_hours", "sum"),
        operating_cost=("operating_cost", "sum"),
    )
)
board["utilization_pct"] = board["volume"] / board["capacity"].replace(0, np.nan) * 100


def status_of(r):
    if r["sla_pct"] < sla_target - 5 or r["backlog"] > backlog_limit * 2.5:
        return "CRITICAL", ROSE
    if r["sla_pct"] < sla_target or r["utilization_pct"] > util_limit or r["backlog"] > backlog_limit:
        return "AT RISK", AMBER
    return "ON TRACK", LIME


for _, r in board.sort_values("sla_pct").iterrows():
    label, colour = status_of(r)
    util = 0 if not np.isfinite(r["utilization_pct"]) else r["utilization_pct"]
    st.markdown(
        f"<div class='row' style='--accent:{colour}'>"
        f"<span class='row-site'>{r['site']}</span>"
        f"<span class='chip'>{label}</span>"
        f"<span class='row-metric'>SLA<b>{r['sla_pct']:.1f}%</b></span>"
        f"<span class='row-metric'>Backlog<b>{r['backlog']:,.0f}</b></span>"
        f"<span class='row-metric'>Overtime<b>{r['overtime_hours']:.0f}h</b></span>"
        f"<span class='row-metric'>Utilisation<b>{util:.0f}%</b></span>"
        f"<span class='bar-track'><span class='bar-fill' "
        f"style='width:{min(util, 130) / 130 * 100:.0f}%'></span></span>"
        f"</div>",
        unsafe_allow_html=True,
    )

# =============================================================
# TABS
# =============================================================
tab_trend, tab_cause, tab_actions, tab_data = st.tabs(
    ["Trends", "Root cause", "Actions", "Data"]
)

trend = (
    f.groupby("date", as_index=False)
    .agg(
        volume=("volume", "sum"),
        capacity=("capacity", "sum"),
        sla_pct=("sla_pct", "mean"),
        backlog=("backlog", "sum"),
        overtime_hours=("overtime_hours", "sum"),
        operating_cost=("operating_cost", "sum"),
    )
    .sort_values("date")
)
trend["cost_per_unit"] = trend["operating_cost"] / trend["volume"].replace(0, np.nan)

with tab_trend:
    c1, c2 = st.columns([1.3, 1])

    with c1:
        fig = go.Figure()
        fig.add_bar(
            x=trend["date"], y=trend["volume"], name="Volume",
            marker_color=CYAN, opacity=0.55,
            hovertemplate="%{x|%d %b}<br>Volume %{y:,.0f}<extra></extra>",
        )
        fig.add_scatter(
            x=trend["date"], y=trend["capacity"], name="Capacity", mode="lines",
            line=dict(color=VIOLET, width=2.5, dash="dot"),
            hovertemplate="%{x|%d %b}<br>Capacity %{y:,.0f}<extra></extra>",
        )
        fig.add_scatter(
            x=trend["date"], y=trend["backlog"], name="Backlog", mode="lines",
            line=dict(color=AMBER, width=2), fill="tozeroy",
            fillcolor="rgba(251,191,36,0.14)", yaxis="y2",
            hovertemplate="%{x|%d %b}<br>Backlog %{y:,.0f}<extra></extra>",
        )
        fig.update_layout(
            title="Demand vs capacity, with backlog build-up",
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Backlog"),
            hovermode="x unified",
        )
        chart(fig, 360)

        breach = trend[trend["sla_pct"] < sla_target]
        fig = go.Figure()
        fig.add_hrect(
            y0=trend["sla_pct"].min() - 1, y1=sla_target,
            fillcolor="rgba(251,113,133,0.10)", line_width=0,
        )
        fig.add_scatter(
            x=trend["date"], y=trend["sla_pct"], name="SLA", mode="lines",
            line=dict(color=LIME, width=2.5, shape="spline"),
            hovertemplate="%{x|%d %b}<br>SLA %{y:.1f}%<extra></extra>",
        )
        fig.add_scatter(
            x=breach["date"], y=breach["sla_pct"], name="Below target", mode="markers",
            marker=dict(color=ROSE, size=9, line=dict(color=INK, width=1)),
            hovertemplate="%{x|%d %b}<br>Missed target: %{y:.1f}%<extra></extra>",
        )
        fig.add_hline(
            y=sla_target, line=dict(color=ROSE, width=1, dash="dash"),
            annotation_text=f"target {sla_target:.1f}%", annotation_font_color=ROSE,
        )
        fig.update_layout(title="Service level against target", hovermode="x unified")
        chart(fig, 300)

    with c2:
        pivot = f.pivot_table(index="site", columns="date", values="sla_pct", aggfunc="mean")
        fig = px.imshow(
            pivot.values,
            x=[pd.Timestamp(c).strftime("%d %b") for c in pivot.columns],
            y=pivot.index.tolist(),
            color_continuous_scale=SLA_SCALE,
            zmin=float(np.nanmin(pivot.values)), zmax=100,
            aspect="auto", labels=dict(color="SLA %"),
        )
        fig.update_traces(hovertemplate="%{y} · %{x}<br>SLA %{z:.1f}%<extra></extra>")
        fig.update_layout(title="Where service dipped, day by day", coloraxis_showscale=True)
        chart(fig, 360, legend=False)

        fig = px.line(
            f.groupby(["date", "site"], as_index=False).agg(
                cost_per_unit=("cost_per_unit", "mean")
            ),
            x="date", y="cost_per_unit", color="site",
            color_discrete_sequence=SITE_SEQ, markers=True,
        )
        fig.update_traces(hovertemplate="%{x|%d %b}<br>₹%{y:,.1f}<extra></extra>")
        fig.update_layout(title="Cost per unit by site", yaxis_title="₹ / unit", xaxis_title="")
        chart(fig, 300)

with tab_cause:
    site_perf = (
        f.groupby("site", as_index=False)
        .agg(
            avg_sla=("sla_pct", "mean"),
            avg_utilization=("utilization_pct", "mean"),
            total_backlog=("backlog", "sum"),
            overtime_hours=("overtime_hours", "sum"),
            avg_cost_per_unit=("cost_per_unit", "mean"),
        )
        .sort_values("avg_sla")
    )
    vendor_perf = (
        f.groupby("vendor", as_index=False)
        .agg(
            avg_sla=("sla_pct", "mean"),
            total_backlog=("backlog", "sum"),
            avg_cost_per_unit=("cost_per_unit", "mean"),
        )
        .sort_values("avg_sla")
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            site_perf, x="avg_sla", y="site", orientation="h",
            color="avg_sla", color_continuous_scale=SLA_SCALE,
            range_color=(min(site_perf["avg_sla"].min(), sla_target - 6), 100),
            text=site_perf["avg_sla"].map(lambda v: f"{v:.1f}%"),
        )
        fig.update_traces(
            textposition="outside", textfont_color=TEXT,
            hovertemplate="%{y}<br>Avg SLA %{x:.1f}%<extra></extra>",
        )
        fig.add_vline(x=sla_target, line_color=ROSE, line_width=1, line_dash="dash")
        fig.update_layout(
            title="Average SLA by site", coloraxis_showscale=False,
            xaxis_title="", yaxis_title="",
        )
        chart(fig, 300, legend=False)

    with c2:
        fig = px.bar(
            vendor_perf, x="avg_sla", y="vendor", orientation="h",
            color="avg_cost_per_unit", color_continuous_scale=["#1D4ED8", VIOLET, ROSE],
            text=vendor_perf["avg_sla"].map(lambda v: f"{v:.1f}%"),
            labels={"avg_cost_per_unit": "₹/unit"},
        )
        fig.update_traces(
            textposition="outside", textfont_color=TEXT,
            hovertemplate="%{y}<br>Avg SLA %{x:.1f}%<br>Cost ₹%{marker.color:,.1f}<extra></extra>",
        )
        fig.add_vline(x=sla_target, line_color=ROSE, line_width=1, line_dash="dash")
        fig.update_layout(
            title="Vendor SLA, shaded by cost per unit", xaxis_title="", yaxis_title=""
        )
        chart(fig, 300, legend=False)

    c1, c2 = st.columns([1.15, 1])
    with c1:
        fig = px.scatter(
            f, x="utilization_pct", y="sla_pct", color="site", size="volume",
            color_discrete_sequence=SITE_SEQ, size_max=20, opacity=0.8,
            hover_data={"date": "|%d %b", "backlog": ":,.0f", "volume": ":,.0f"},
        )
        fig.add_vline(x=util_limit, line_color=VIOLET, line_width=1, line_dash="dash")
        fig.add_hline(y=sla_target, line_color=ROSE, line_width=1, line_dash="dash")
        fig.update_layout(
            title="Does load explain the misses? Each dot is one site-day",
            xaxis_title="Utilisation %", yaxis_title="SLA %",
        )
        chart(fig, 380)

        corr = f[["utilization_pct", "sla_pct"]].dropna()
        if len(corr) > 2:
            r = corr["utilization_pct"].corr(corr["sla_pct"])
            verdict = (
                "load is the main driver" if r < -0.4
                else "load explains part of it" if r < -0.15
                else "load is not the driver — look at process or vendor"
            )
            st.caption(f"Utilisation vs SLA correlation: **{r:+.2f}** — {verdict}.")

    with c2:
        tm = (
            f.groupby(["site", "vendor"], as_index=False)
            .agg(backlog=("backlog", "sum"), avg_sla=("sla_pct", "mean"))
        )
        tm = tm[tm["backlog"] > 0]
        if tm.empty:
            st.info("No backlog recorded in this selection.")
        else:
            fig = px.treemap(
                tm, path=[px.Constant("All sites"), "site", "vendor"],
                values="backlog", color="avg_sla",
                color_continuous_scale=SLA_SCALE,
                range_color=(tm["avg_sla"].min(), 100),
            )
            fig.update_traces(
                marker_line_color=INK, marker_line_width=2,
                hovertemplate="%{label}<br>Backlog %{value:,.0f}<br>Avg SLA %{color:.1f}%<extra></extra>",
            )
            fig.update_layout(title="Where the backlog sits — size is volume, colour is SLA")
            chart(fig, 380, legend=False)

    st.markdown("<p class='board-title'>Site detail</p>", unsafe_allow_html=True)
    st.dataframe(
        site_perf,
        use_container_width=True,
        hide_index=True,
        column_config={
            "site": st.column_config.TextColumn("Site"),
            "avg_sla": st.column_config.ProgressColumn(
                "Avg SLA", format="%.1f%%", min_value=70, max_value=100
            ),
            "avg_utilization": st.column_config.NumberColumn("Avg utilisation", format="%.1f%%"),
            "total_backlog": st.column_config.NumberColumn("Backlog", format="%d"),
            "overtime_hours": st.column_config.NumberColumn("Overtime (h)", format="%.0f"),
            "avg_cost_per_unit": st.column_config.NumberColumn("Cost / unit", format="₹%.1f"),
        },
    )

with tab_actions:
    ex = (
        cur.groupby(["site", "vendor"], as_index=False)
        .agg(
            volume=("volume", "sum"),
            capacity=("capacity", "sum"),
            sla_pct=("sla_pct", "mean"),
            backlog=("backlog", "sum"),
            overtime_hours=("overtime_hours", "sum"),
        )
    )
    ex["utilization_pct"] = ex["volume"] / ex["capacity"].replace(0, np.nan) * 100

    rows = []
    for _, r in ex.iterrows():
        if r["sla_pct"] < sla_target - 5:
            rows.append((
                "Critical", r["site"], r["vendor"],
                f"SLA at {r['sla_pct']:.1f}% against a {sla_target:.1f}% target.",
                "Pull the exception log by process stage and vendor today; "
                "escalate the worst stage to the vendor lead.",
            ))
        elif r["sla_pct"] < sla_target:
            rows.append((
                "High", r["site"], r["vendor"],
                f"SLA at {r['sla_pct']:.1f}%, short of target.",
                "Check backlog ageing and roster coverage against hourly demand.",
            ))
        if np.isfinite(r["utilization_pct"]) and r["utilization_pct"] > util_limit:
            rows.append((
                "Critical" if r["utilization_pct"] > util_limit + 10 else "High",
                r["site"], r["vendor"],
                f"Demand is {r['utilization_pct']:.0f}% of capacity.",
                "Add a temporary shift or move volume to the nearest site with headroom.",
            ))
        if r["backlog"] > backlog_limit * 2.5:
            rows.append((
                "Critical", r["site"], r["vendor"],
                f"Backlog at {r['backlog']:,.0f}.",
                "Clear oldest and highest-value work first; review cut-off rules.",
            ))
        elif r["backlog"] > backlog_limit:
            rows.append((
                "Medium", r["site"], r["vendor"],
                f"Backlog at {r['backlog']:,.0f}, above the {backlog_limit} alert.",
                "Set a clearance target for tomorrow and confirm staffing to hit it.",
            ))
        if r["overtime_hours"] > overtime_limit:
            rows.append((
                "Medium", r["site"], r["vendor"],
                f"Overtime at {r['overtime_hours']:.0f} hours.",
                "Compare roster shape to the hourly demand curve before approving more.",
            ))

    if not rows:
        st.success(
            f"Nothing breaches your thresholds on {pd.Timestamp(as_of).strftime('%d %b')}. "
            "Tighten the sliders on the left to stress-test the operation."
        )
    else:
        act = pd.DataFrame(rows, columns=["priority", "site", "vendor", "finding", "action"])
        order = ["Critical", "High", "Medium"]
        act["priority"] = pd.Categorical(act["priority"], categories=order, ordered=True)
        act = act.sort_values(["priority", "site"])

        counts = act["priority"].value_counts().reindex(order).fillna(0)
        cols = st.columns(3)
        for col, name, colour in zip(cols, order, [ROSE, AMBER, CYAN]):
            kpi(col, f"{name} actions", f"{int(counts[name])}", colour)

        fig = px.bar(
            act.groupby(["site", "priority"], observed=True).size().reset_index(name="n"),
            x="n", y="site", color="priority", orientation="h",
            color_discrete_map={"Critical": ROSE, "High": AMBER, "Medium": CYAN},
        )
        fig.update_layout(title="Open actions by site", xaxis_title="", yaxis_title="")
        chart(fig, 240)

        for p, colour in zip(order, [ROSE, AMBER, CYAN]):
            block = act[act["priority"] == p]
            if block.empty:
                continue
            with st.expander(f"{p} · {len(block)} action(s)", expanded=(p == "Critical")):
                for _, r in block.iterrows():
                    st.markdown(
                        f"<div class='row' style='--accent:{colour}; display:block'>"
                        f"<span class='row-site'>{r['site']}</span> "
                        f"<span class='chip'>{r['vendor']}</span><br>"
                        f"<span style='color:{TEXT}; font-size:13.5px'>{r['finding']}</span><br>"
                        f"<span style='color:{MUTED}; font-size:13px'>→ {r['action']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        st.download_button(
            "Download action list",
            data=act.to_csv(index=False).encode("utf-8"),
            file_name=f"actions_{pd.Timestamp(as_of).date()}.csv",
            mime="text/csv",
        )

with tab_data:
    st.markdown("<p class='board-title'>Filtered records</p>", unsafe_allow_html=True)
    view = f.sort_values("date", ascending=False).copy()
    view["date"] = view["date"].dt.date
    st.dataframe(
        view[[
            "date", "site", "vendor", "volume", "capacity", "utilization_pct",
            "sla_pct", "backlog", "overtime_hours", "cost_per_unit", "operating_cost",
        ]],
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "utilization_pct": st.column_config.NumberColumn("Utilisation", format="%.1f%%"),
            "sla_pct": st.column_config.ProgressColumn(
                "SLA", format="%.1f%%", min_value=70, max_value=100
            ),
            "cost_per_unit": st.column_config.NumberColumn("Cost / unit", format="₹%.1f"),
            "operating_cost": st.column_config.NumberColumn("Operating cost", format="₹%.0f"),
        },
    )
    c1, c2 = st.columns(2)
    c1.download_button(
        "Download filtered data",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="operations_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )
    c2.download_button(
        "Download CSV template",
        data=pd.DataFrame(columns=REQUIRED).to_csv(index=False).encode("utf-8"),
        file_name="operations_control_tower_template.csv",
        mime="text/csv",
        use_container_width=True,
    )

# =============================================================
# FOOTER
# =============================================================
st.markdown(
f"""<div style="text-align:center; padding:26px 0 20px 0; border-top:1px solid {LINE}; margin-top:28px;">
<div style="font-family:'JetBrains Mono',monospace; font-size:12px; letter-spacing:.14em; text-transform:uppercase; color:{MUTED};">
Operations Intelligence Control Tower · Vikrant Thenge
</div>
<div style="display:flex; justify-content:center; align-items:center; gap:22px; flex-wrap:wrap; margin-top:12px; font-size:13px;">
<a href="mailto:vikrantthenge@outlook.com" style="color:#0078D4; text-decoration:none; display:inline-flex; align-items:center; gap:7px;">
<i class="fa-solid fa-envelope" style="font-size:15px;"></i> Email
</a>
<a href="https://www.linkedin.com/in/vthenge" target="_blank" style="color:#0A66C2; text-decoration:none; display:inline-flex; align-items:center; gap:7px;">
<i class="fa-brands fa-linkedin" style="font-size:16px;"></i> LinkedIn
</a>
<a href="https://github.com/Vikrantthenge/Apps" target="_blank" style="color:#FFFFFF; font-weight:600; text-decoration:none; display:inline-flex; align-items:center; gap:7px;">
<i class="fa-brands fa-github" style="font-size:16px; color:#181717; background:#E6EDF7; border-radius:50%; width:20px; height:20px; display:inline-flex; align-items:center; justify-content:center;"></i> GitHub
</a>
</div>
<div style="font-size:11px; color:{MUTED}; opacity:.75; margin-top:10px;">
© 2026 Vikrant Thenge
</div>
</div>""",
    unsafe_allow_html=True,
)
