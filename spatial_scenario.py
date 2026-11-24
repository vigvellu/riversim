
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="RiverSim | Spatial Simulator",
    page_icon="🌊",
    layout="wide"
)

DATA = Path("data/raw")
REPORTS = Path("outputs/reports")

st.title("🌊 RiverSim — Spatial Scenario Simulator")

st.caption(
    "Explore hypothetical future channel evolution "
    "using transect-specific historical migration rates."
)

st.warning(
    "This is an exploratory constant-rate scenario model, "
    "not a validated prediction of future river behaviour. "
    "Results depend on the quality of the historical measurements."
)

# ==========================================
# LOAD DATA
# ==========================================

@st.cache_data
def load_data():

    points = gpd.read_file(
        DATA / "bank_points.gpkg"
    )

    migration = pd.read_csv(
        REPORTS / "migration_rates.csv"
    )

    transects = gpd.read_file(
        DATA / "transects.gpkg"
    )

    return points, migration, transects


try:

    points, migration, transects = load_data()

except Exception as error:

    st.error(f"Could not load project data: {error}")
    st.stop()


# ==========================================
# VALIDATE DATA
# ==========================================

required_migration_columns = {
    "transect_id",
    "start_year",
    "end_year",
    "bank",
    "migration_rate_m_per_year"
}

if not required_migration_columns.issubset(
    migration.columns
):

    st.error(
        "The migration CSV is missing required columns."
    )
    st.stop()


# ==========================================
# SELECT HISTORICAL PERIOD
# ==========================================

st.sidebar.header("Historical Data")

intervals = sorted(
    migration[
        ["start_year", "end_year"]
    ].drop_duplicates().itertuples(
        index=False,
        name=None
    )
)

selected = st.sidebar.selectbox(
    "Historical migration period",
    intervals,
    format_func=lambda x: f"{x[0]}–{x[1]}"
)


# ==========================================
# SIMULATION CONTROLS
# ==========================================

st.sidebar.divider()
st.sidebar.header("Simulation Controls")

duration = st.sidebar.slider(
    "Future simulation duration",
    min_value=1,
    max_value=30,
    value=10,
    help="Number of years after the 2025 baseline."
)

rate_multiplier = st.sidebar.slider(
    "Migration rate multiplier",
    min_value=0.0,
    max_value=2.0,
    value=0.5,
    step=0.1,
    help="0 = no movement, 1 = historical rate, 2 = twice the historical rate."
)

st.sidebar.caption(
    "All future scenarios start from the 2025 measurements."
)


# ==========================================
# PREPARE 2025 BASELINE
# ==========================================

baseline_points = points[
    points["year"] == 2025
].copy()

baseline = baseline_points.pivot(
    index="transect_id",
    columns="bank",
    values="distance_m"
).reset_index()

baseline.columns.name = None

baseline = baseline.rename(
    columns={
        "north": "north_initial",
        "south": "south_initial"
    }
)

if not {
    "north_initial",
    "south_initial"
}.issubset(baseline.columns):

    st.error(
        "Could not find both north and south "
        "bank measurements for 2025."
    )
    st.stop()

baseline["initial_width"] = (
    baseline["south_initial"]
    - baseline["north_initial"]
)


# ==========================================
# PREPARE HISTORICAL MIGRATION RATES
# ==========================================

historical_rates = migration[
    (migration["start_year"] == selected[0]) &
    (migration["end_year"] == selected[1])
].pivot(
    index="transect_id",
    columns="bank",
    values="migration_rate_m_per_year"
).reset_index()

historical_rates.columns.name = None

historical_rates = historical_rates.rename(
    columns={
        "north": "north_rate",
        "south": "south_rate"
    }
)

if not {
    "north_rate",
    "south_rate"
}.issubset(historical_rates.columns):

    st.error(
        "Both north and south migration rates "
        "are required for the selected period."
    )
    st.stop()


# ==========================================
# COMBINE BASELINE AND RATES
# ==========================================

model = baseline.merge(
    historical_rates,
    on="transect_id",
    how="inner"
)

if len(model) != len(baseline):

    st.error(
        "Some transects are missing historical migration rates."
    )
    st.stop()

if model[
    ["north_rate", "south_rate"]
].isna().any().any():

    st.error(
        "Missing migration rates detected. "
        "Check your historical data."
    )
    st.stop()


# ==========================================
# SPATIAL REFERENCE VALIDATION
# ==========================================

transect_lookup = transects.set_index(
    "transect_id"
).geometry

missing_transects = set(
    model["transect_id"]
) - set(transect_lookup.index)

if missing_transects:

    st.error(
        f"Missing transect geometries: {missing_transects}"
    )
    st.stop()


# ==========================================
# RUN SIMULATION
# ==========================================

records = []

for year in range(duration + 1):

    elapsed = year

    for _, row in model.iterrows():

        north_position = (
            row["north_initial"]
            + row["north_rate"]
            * rate_multiplier
            * elapsed
        )

        south_position = (
            row["south_initial"]
            + row["south_rate"]
            * rate_multiplier
            * elapsed
        )

        width = south_position - north_position

        records.append({

            "year": 2025 + elapsed,

            "transect_id": row["transect_id"],

            "north_position": north_position,

            "south_position": south_position,

            "channel_width": width

        })


results = pd.DataFrame(records)


# ==========================================
# SIMULATION SUMMARY
# ==========================================

initial_mean = model[
    "initial_width"
].mean()

final_results = results[
    results["year"] == 2025 + duration
]

final_mean = final_results[
    "channel_width"
].mean()

width_change = final_mean - initial_mean

st.header("Simulation Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Baseline Year",
    "2025"
)

col2.metric(
    "Simulation End",
    str(2025 + duration)
)

col3.metric(
    "Initial Mean Width",
    f"{initial_mean:.2f} m"
)

col4.metric(
    "Final Mean Width",
    f"{final_mean:.2f} m"
)

st.metric(
    "Mean Channel Width Change",
    f"{width_change:+.2f} m",
    delta=f"{width_change:+.2f} m"
)


# ==========================================
# INVALID CHANNEL DETECTION
# ==========================================

st.divider()

st.subheader("Geometric Validity Check")

invalid = results[
    results["channel_width"] <= 0
]

if invalid.empty:

    st.success(
        "No zero-width or negative-width transects "
        "were detected in this scenario."
    )

else:

    st.error(
        f"{invalid['transect_id'].nunique()} transects "
        "have zero or negative simulated channel width."
    )

    st.dataframe(
        invalid,
        width="stretch",
        hide_index=True
    )


# ==========================================
# MEAN CHANNEL WIDTH EVOLUTION
# ==========================================

st.divider()

st.header("Channel Width Evolution")

summary = (
    results.groupby("year")["channel_width"]
    .mean()
    .reset_index()
)

fig = px.line(
    summary,
    x="year",
    y="channel_width",
    markers=True,
    title="Mean Simulated Channel Width"
)

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Mean channel width (m)",
    template="plotly_white"
)

st.plotly_chart(
    fig,
    width="stretch"
)


# ==========================================
# INDIVIDUAL TRANSECT EVOLUTION
# ==========================================

st.divider()

st.header("Individual Transect Analysis")

fig2 = px.line(
    results,
    x="year",
    y="channel_width",
    color="transect_id",
    markers=True,
    title="Channel Width Evolution by Transect"
)

fig2.update_layout(
    xaxis_title="Year",
    yaxis_title="Channel width (m)",
    legend_title="Transect"
)

st.plotly_chart(
    fig2,
    width="stretch"
)


# ==========================================
# TRANSECT EXPLORER
# ==========================================

st.subheader("Explore Individual Transect")

selected_transect = st.selectbox(
    "Choose a transect",
    sorted(results["transect_id"].unique())
)

individual = results[
    results["transect_id"] == selected_transect
]

st.line_chart(
    individual,
    x="year",
    y="channel_width"
)

st.dataframe(
    individual,
    width="stretch",
    hide_index=True
)


# ==========================================
# FUTURE SPATIAL MAP
# ==========================================

st.divider()

st.header("Hypothetical Future Channel Map")

st.caption(
    "Dashed lines show the measured 2025 bank points. "
    "Solid lines show the simulated bank positions."
)

available_years = sorted(
    results["year"].unique()
)

map_year = st.select_slider(
    "Select simulation year",
    options=available_years,
    value=available_years[-1]
)

map_records = []

for _, row in model.iterrows():

    line = transect_lookup.loc[
        row["transect_id"]
    ]

    # The projected distance along each transect
    # was found to equal distance_m + 300 m.
    north_distance = (
        row["north_initial"]
        + 300
        + row["north_rate"]
        * rate_multiplier
        * (map_year - 2025)
    )

    south_distance = (
        row["south_initial"]
        + 300
        + row["south_rate"]
        * rate_multiplier
        * (map_year - 2025)
    )

    # Keep interpolation distances within the transect.
    north_distance = max(
        0,
        min(north_distance, line.length)
    )

    south_distance = max(
        0,
        min(south_distance, line.length)
    )

    north_point = line.interpolate(
        north_distance
    )

    south_point = line.interpolate(
        south_distance
    )

    map_records.append({

        "transect_id": row["transect_id"],

        "bank": "north",

        "x": north_point.x,

        "y": north_point.y

    })

    map_records.append({

        "transect_id": row["transect_id"],

        "bank": "south",

        "x": south_point.x,

        "y": south_point.y

    })


map_data = pd.DataFrame(map_records)


# ==========================================
# CREATE SPATIAL MAP
# ==========================================

fig_map = go.Figure()

original = baseline_points.copy()

for bank in ["north", "south"]:

    original_bank = original[
        original["bank"] == bank
    ].sort_values("transect_id")

    # Original 2025 bank points
    fig_map.add_trace(
        go.Scatter(
            x=original_bank.geometry.x,
            y=original_bank.geometry.y,
            mode="markers",
            name=f"2025 {bank.title()} bank",
            marker=dict(size=7),
            hovertext=original_bank["transect_id"],
            hovertemplate=(
                "Transect: %{hovertext}<br>"
                "Easting: %{x:.2f}<br>"
                "Northing: %{y:.2f}"
                "<extra></extra>"
            )
        )
    )

    # Simulated future bank positions
    future_bank = map_data[
        map_data["bank"] == bank
    ].sort_values("transect_id")

    fig_map.add_trace(
        go.Scatter(
            x=future_bank["x"],
            y=future_bank["y"],
            mode="lines+markers",
            name=f"{map_year} scenario {bank.title()} bank",
            line=dict(width=3),
            marker=dict(size=6),
            hovertext=future_bank["transect_id"],
            hovertemplate=(
                "Transect: %{hovertext}<br>"
                "Easting: %{x:.2f}<br>"
                "Northing: %{y:.2f}"
                "<extra></extra>"
            )
        )
    )


fig_map.update_layout(
    title=(
        f"2025 vs Hypothetical {map_year} "
        "Bank Positions"
    ),
    xaxis_title="Easting (m)",
    yaxis_title="Northing (m)",
    template="plotly_white",
    height=750,
    yaxis=dict(
        scaleanchor="x",
        scaleratio=1
    ),
    legend_title="Bank positions"
)

st.plotly_chart(
    fig_map,
    width="stretch"
)

# ==========================================
# SCENARIO COMPARISON
# ==========================================

st.divider()

st.header("Scenario Comparison")

st.write(
    "Compare how different migration-rate assumptions "
    "could influence future channel width."
)

scenario_multipliers = {
    "Conservative (50%)": 0.5,
    "Baseline (100%)": 1.0,
    "Accelerated (150%)": 1.5
}

scenario_records = []

for scenario_name, multiplier in scenario_multipliers.items():

    for year in range(duration + 1):

        for _, row in model.iterrows():

            north_position = (
                row["north_initial"]
                + row["north_rate"] * multiplier * year
            )

            south_position = (
                row["south_initial"]
                + row["south_rate"] * multiplier * year
            )

            width = south_position - north_position

            scenario_records.append({

                "scenario": scenario_name,

                "year": 2025 + year,

                "transect_id": row["transect_id"],

                "channel_width": width

            })


scenario_results = pd.DataFrame(
    scenario_records
)

scenario_summary = (
    scenario_results
    .groupby(["scenario", "year"])["channel_width"]
    .mean()
    .reset_index()
)

# Comparison chart

fig_scenarios = px.line(
    scenario_summary,
    x="year",
    y="channel_width",
    color="scenario",
    markers=True,
    title="Future Channel Width Under Different Scenarios"
)

fig_scenarios.update_layout(
    xaxis_title="Year",
    yaxis_title="Mean channel width (m)",
    template="plotly_white",
    legend_title="Scenario"
)

st.plotly_chart(
    fig_scenarios,
    width="stretch"
)

# Final-year comparison

st.subheader("Final-Year Scenario Comparison")

final_scenarios = scenario_summary[
    scenario_summary["year"] == 2025 + duration
].copy()

final_scenarios = final_scenarios.rename(
    columns={
        "scenario": "Scenario",
        "year": "Year",
        "channel_width": "Mean channel width (m)"
    }
)

st.dataframe(
    final_scenarios,
    width="stretch",
    hide_index=True
)

# Scenario comparison export

scenario_csv = scenario_results.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download All Scenario Comparisons (CSV)",
    data=scenario_csv,
    file_name="riversim_scenario_comparison.csv",
    mime="text/csv"
)


# ==========================================
# EXPORT RESULTS
# ==========================================

st.divider()

st.header("Export Simulation Results")

csv = results.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Simulation Results (CSV)",
    data=csv,
    file_name="riversim_spatial_scenario.csv",
    mime="text/csv"
)


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "RiverSim | Spatially varying constant-rate "
    "scenario model | EPSG:32645"
)
