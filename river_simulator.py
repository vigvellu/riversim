
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="RiverSim | Scenario Simulator",
    page_icon="🌊",
    layout="wide"
)

DATA_DIR = Path("data/raw")

@st.cache_data
def load_points():
    return gpd.read_file(
        DATA_DIR / "bank_points.gpkg"
    )

points = load_points()

st.title("🌊 RiverSim — Scenario Simulator")

st.caption(
    "Explore hypothetical future channel changes "
    "using the 2025 bank measurements."
)

st.warning(
    "This is a simplified exploratory model. "
    "It assumes constant movement rates and does "
    "not account for hydrology, sediment transport, "
    "floods, engineering works or other physical processes."
)

# ======================================
# SIDEBAR PARAMETERS
# ======================================

st.sidebar.header("Simulation Parameters")

north_rate = st.sidebar.slider(
    "North bank movement (m/year)",
    -50.0, 50.0, 5.0, 1.0
)

south_rate = st.sidebar.slider(
    "South bank movement (m/year)",
    -50.0, 50.0, 5.0, 1.0
)

duration = st.sidebar.slider(
    "Simulation duration (years)",
    1, 50, 10
)

# ======================================
# PREPARE 2025 BASELINE
# ======================================

baseline = points[
    points["year"] == 2025
].pivot(
    index="transect_id",
    columns="bank",
    values="distance_m"
).reset_index()

baseline["initial_width"] = (
    baseline["south"] - baseline["north"]
)

# ======================================
# SIMULATE FUTURE POSITIONS
# ======================================

records = []

for year in range(duration + 1):

    north_position = (
        baseline["north"] + north_rate * year
    )

    south_position = (
        baseline["south"] + south_rate * year
    )

    width = south_position - north_position

    for i, transect in baseline.iterrows():

        records.append({
            "year": 2025 + year,
            "transect_id": transect["transect_id"],
            "north_position": north_position.iloc[i],
            "south_position": south_position.iloc[i],
            "channel_width": width.iloc[i]
        })

results = pd.DataFrame(records)

# ======================================
# SUMMARY
# ======================================

final_results = results[
    results["year"] == 2025 + duration
]

initial_mean = baseline["initial_width"].mean()

final_mean = final_results["channel_width"].mean()

width_change = final_mean - initial_mean

col1, col2, col3 = st.columns(3)

col1.metric(
    "Initial Mean Width",
    f"{initial_mean:.2f} m"
)

col2.metric(
    "Final Mean Width",
    f"{final_mean:.2f} m"
)

col3.metric(
    "Total Width Change",
    f"{width_change:+.2f} m"
)

# ======================================
# WIDTH EVOLUTION
# ======================================

st.subheader("Simulated Channel Width Evolution")

summary = (
    results.groupby("year")["channel_width"]
    .mean()
    .reset_index()
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=summary["year"],
        y=summary["channel_width"],
        mode="lines+markers",
        name="Mean channel width"
    )
)

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Mean channel width (m)",
    template="plotly_white"
)

st.plotly_chart(fig, width="stretch")

# ======================================
# TRANSECT COMPARISON
# ======================================

st.subheader("Individual Transect Simulation")

selected_transect = st.selectbox(
    "Choose transect",
    sorted(results["transect_id"].unique())
)

transect_data = results[
    results["transect_id"] == selected_transect
]

fig2 = go.Figure()

fig2.add_trace(
    go.Scatter(
        x=transect_data["year"],
        y=transect_data["channel_width"],
        mode="lines+markers",
        name="Simulated width"
    )
)

fig2.update_layout(
    title=f"Transect {selected_transect}",
    xaxis_title="Year",
    yaxis_title="Channel width (m)",
    template="plotly_white"
)

st.plotly_chart(fig2, width="stretch")

# ======================================
# DATA TABLE
# ======================================

st.subheader("Simulation Results")

st.dataframe(
    results,
    width="stretch",
    hide_index=True
)

# ======================================
# EXPORT
# ======================================

csv = results.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Simulation Results (CSV)",
    data=csv,
    file_name="riversim_scenario.csv",
    mime="text/csv"
)

st.caption(
    "RiverSim | Simplified constant-rate scenario model"
)
