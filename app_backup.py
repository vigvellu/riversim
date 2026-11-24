
import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

# -----------------------------
# CONFIGURATION
# -----------------------------

st.set_page_config(
    page_title="RiverSim | Padma River",
    page_icon="🌊",
    layout="wide"
)

DATA = Path("data/raw")
REPORTS = Path("outputs/reports")

st.title("RiverSim")
st.caption(
    "Interactive River Migration Simulator | "
    "Padma River, Rajshahi"
)

st.warning(
    "Exploratory analysis: measurements and "
    "erosion/accretion interpretations require "
    "further imagery and methodology validation."
)

# -----------------------------
# LOAD DATA
# -----------------------------

@st.cache_data
def load_data():

    water = gpd.read_file(
        DATA / "water_polygons.gpkg"
    )

    migration = pd.read_csv(
        REPORTS / "migration_rates.csv"
    )

    nsm = pd.read_csv(
        REPORTS / "nsm_epr_results.csv"
    )

    channel = pd.read_csv(
        REPORTS / "channel_change_results.csv"
    )

    transects = gpd.read_file(
        DATA / "transects.gpkg"
    )

    return water, migration, nsm, channel, transects


try:
    water, migration, nsm, channel, transects = load_data()

except Exception as error:
    st.error(f"Could not load project data: {error}")
    st.stop()

# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title("RiverSim Controls")

page = st.sidebar.radio(
    "Select analysis",
    [
        "Overview",
        "Bank Migration",
        "Channel Morphology",
        "Spatial Analysis"
    ]
)

# -----------------------------
# OVERVIEW
# -----------------------------

if page == "Overview":

    st.header("Study Overview")

    total_area = water.groupby("year")[
        "area_km2"
    ].sum()

    latest_area = total_area.loc[2025]

    mean_north = nsm[
        nsm["bank"] == "north"
    ]["NSM_m"].mean()

    mean_south = nsm[
        nsm["bank"] == "south"
    ]["NSM_m"].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Observation Years", "6")
    col2.metric("Transects", "19")
    col3.metric(
        "2025 Water Area",
        f"{latest_area:.2f} km²"
    )
    col4.metric("Analysis Period", "35 years")

    st.subheader("Historical Water Area")

    area_df = total_area.rename(
        "Area (km²)"
    ).reset_index()

    st.line_chart(
        area_df,
        x="year",
        y="Area (km²)"
    )

    st.subheader("Long-term Bank Displacement")

    col1, col2 = st.columns(2)

    col1.metric(
        "North Bank Mean NSM",
        f"{mean_north:.2f} m"
    )

    col2.metric(
        "South Bank Mean NSM",
        f"{mean_south:.2f} m"
    )

# -----------------------------
# BANK MIGRATION
# -----------------------------

elif page == "Bank Migration":

    st.header("Bank Migration Analysis")

    intervals = sorted(
        migration[
            ["start_year", "end_year"]
        ].drop_duplicates().itertuples(
            index=False, name=None
        )
    )

    selected = st.selectbox(
        "Select observation period",
        intervals,
        format_func=lambda x: f"{x[0]}–{x[1]}"
    )

    bank = st.selectbox(
        "Select bank",
        ["north", "south"]
    )

    selected_data = migration[
        (migration["start_year"] == selected[0]) &
        (migration["end_year"] == selected[1]) &
        (migration["bank"] == bank)
    ].sort_values("transect_id")

    st.subheader(
        f"{bank.title()} Bank: {selected[0]}–{selected[1]}"
    )

    st.line_chart(
        selected_data,
        x="transect_id",
        y="migration_rate_m_per_year"
    )

    st.dataframe(
        selected_data,
        use_container_width=True,
        hide_index=True
    )

# -----------------------------
# CHANNEL MORPHOLOGY
# -----------------------------

elif page == "Channel Morphology":

    st.header("Channel Morphology")

    intervals = sorted(
        channel[
            ["start_year", "end_year"]
        ].drop_duplicates().itertuples(
            index=False, name=None
        )
    )

    selected = st.selectbox(
        "Select observation period",
        intervals,
        format_func=lambda x: f"{x[0]}–{x[1]}"
    )

    selected_data = channel[
        (channel["start_year"] == selected[0]) &
        (channel["end_year"] == selected[1])
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean Width Change",
        f"{selected_data['width_change_m'].mean():.2f} m"
    )

    col2.metric(
        "Mean Width Change Rate",
        f"{selected_data['width_change_rate_m_per_year'].mean():.2f} m/year"
    )

    col3.metric(
        "Mean Centre Shift",
        f"{selected_data['centre_shift_m'].mean():.2f} m"
    )

    st.subheader("Width Change by Transect")

    st.bar_chart(
        selected_data,
        x="transect_id",
        y="width_change_m"
    )

    st.subheader("Centre Shift by Transect")

    st.bar_chart(
        selected_data,
        x="transect_id",
        y="centre_shift_m"
    )

    st.dataframe(
        selected_data,
        use_container_width=True,
        hide_index=True
    )

# -----------------------------
# SPATIAL ANALYSIS
# -----------------------------

elif page == "Spatial Analysis":

    st.header("Spatial Migration Distribution")

    intervals = sorted(
        migration[
            ["start_year", "end_year"]
        ].drop_duplicates().itertuples(
            index=False, name=None
        )
    )

    selected = st.selectbox(
        "Select period",
        intervals,
        format_func=lambda x: f"{x[0]}–{x[1]}"
    )

    bank = st.selectbox(
        "Select bank",
        ["north", "south"]
    )

    selected_data = migration[
        (migration["start_year"] == selected[0]) &
        (migration["end_year"] == selected[1]) &
        (migration["bank"] == bank)
    ]

    # Join migration measurements to transects
    spatial_data = transects.merge(
        selected_data,
        on="transect_id"
    )

    fig, ax = plt.subplots(figsize=(10, 8))

    spatial_data.plot(
        ax=ax,
        column="migration_rate_m_per_year",
        cmap="RdYlBu_r",
        legend=True,
        linewidth=3,
        legend_kwds={
            "label": "Migration rate (m/year)"
        }
    )

    ax.set_title(
        f"{bank.title()} Bank: "
        f"{selected[0]}–{selected[1]}"
    )

    ax.set_aspect("equal")
    ax.set_axis_off()

    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "Colours represent signed along-transect "
        "migration rates, not independently "
        "verified erosion or accretion."
    )

    st.dataframe(
        selected_data,
        use_container_width=True,
        hide_index=True
    )

# -----------------------------
# FOOTER
# -----------------------------

st.divider()

st.caption(
    "RiverSim | Exploratory river morphology "
    "analysis | EPSG:32645"
)
