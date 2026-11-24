
import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="RiverSim | Padma River",
    page_icon="🌊",
    layout="wide"
)

DATA = Path("data/raw")
REPORTS = Path("outputs/reports")

st.title("🌊 RiverSim")
st.caption(
    "Interactive River Migration Simulator | "
    "Padma River, Rajshahi"
)

st.warning(
    "Exploratory analysis: measurements and "
    "erosion/accretion interpretations require "
    "further imagery and methodology validation."
)

# ==========================================
# LOAD DATA
# ==========================================

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


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_intervals(df):

    return sorted(
        df[["start_year", "end_year"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )


def interval_label(interval):

    return f"{interval[0]}–{interval[1]}"


# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("RiverSim Controls")

page = st.sidebar.radio(
    "Select analysis",
    [
        "Overview",
        "Bank Migration",
        "Erosion & Accretion",
        "Channel Morphology",
        "Spatial Analysis",
        "Transect Explorer"
    ]
)


# ==========================================
# OVERVIEW
# ==========================================

if page == "Overview":

    st.header("Study Overview")

    total_area = (
        water.groupby("year")["area_km2"]
        .sum()
        .sort_index()
    )

    latest_area = total_area.loc[2025]

    mean_north = nsm[
        nsm["bank"] == "north"
    ]["NSM_m"].mean()

    mean_south = nsm[
        nsm["bank"] == "south"
    ]["NSM_m"].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Observation Years", "6")
    col2.metric("Transects", str(len(transects)))
    col3.metric(
        "2025 Water Area",
        f"{latest_area:.2f} km²"
    )
    col4.metric("Analysis Period", "35 years")

    st.divider()

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

    st.divider()

    st.subheader("Observation Data")

    st.write("Available observation years:")

    st.write(
        sorted(water["year"].unique().tolist())
    )

    st.write(
        f"Total water polygon records: {len(water)}"
    )

    st.write(
        f"Total bank migration measurements: {len(migration)}"
    )


# ==========================================
# BANK MIGRATION
# ==========================================

elif page == "Bank Migration":

    st.header("Bank Migration Analysis")

    intervals = get_intervals(migration)

    selected = st.selectbox(
        "Select observation period",
        intervals,
        format_func=interval_label
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
        f"{bank.title()} Bank: {interval_label(selected)}"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean Migration Rate",
        f"{selected_data['migration_rate_m_per_year'].mean():.2f} m/year"
    )

    col2.metric(
        "Maximum Rate",
        f"{selected_data['migration_rate_m_per_year'].max():.2f} m/year"
    )

    col3.metric(
        "Minimum Rate",
        f"{selected_data['migration_rate_m_per_year'].min():.2f} m/year"
    )

    st.subheader("Migration Rate by Transect")

    st.bar_chart(
        selected_data,
        x="transect_id",
        y="migration_rate_m_per_year"
    )

    st.dataframe(
        selected_data,
        width="stretch",
        hide_index=True
    )

    st.caption(
        "Rates represent signed displacement along transects. "
        "Positive and negative values do not automatically "
        "mean erosion or accretion on both banks."
    )


# ==========================================
# EROSION AND ACCRETION
# ==========================================

elif page == "Erosion & Accretion":

    st.header("Provisional Erosion & Accretion")

    st.info(
        "Interpretation convention: positive values indicate "
        "landward retreat; negative values indicate "
        "channelward advance. This convention differs "
        "between the north and south banks."
    )

    intervals = get_intervals(migration)

    selected = st.selectbox(
        "Select observation period",
        intervals,
        format_func=interval_label
    )

    bank = st.selectbox(
        "Select bank",
        ["north", "south"]
    )

    selected_data = migration[
        (migration["start_year"] == selected[0]) &
        (migration["end_year"] == selected[1]) &
        (migration["bank"] == bank)
    ].copy()

    # Convert signed transect movement into
    # provisional landward retreat rates.
    if bank == "north":
        selected_data["landward_rate"] = (
            -selected_data["migration_rate_m_per_year"]
        )
    else:
        selected_data["landward_rate"] = (
            selected_data["migration_rate_m_per_year"]
        )

    selected_data["interpretation"] = (
        selected_data["landward_rate"]
        .apply(
            lambda x:
            "Retreat" if x > 0
            else "Advance" if x < 0
            else "Stable"
        )
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean Landward Rate",
        f"{selected_data['landward_rate'].mean():.2f} m/year"
    )

    col2.metric(
        "Retreat Transects",
        str((selected_data["interpretation"] == "Retreat").sum())
    )

    col3.metric(
        "Advance Transects",
        str((selected_data["interpretation"] == "Advance").sum())
    )

    st.subheader("Retreat and Advance by Transect")

    st.bar_chart(
        selected_data,
        x="transect_id",
        y="landward_rate"
    )

    st.subheader("Classification")

    st.dataframe(
        selected_data[
            [
                "transect_id",
                "migration_rate_m_per_year",
                "landward_rate",
                "interpretation"
            ]
        ],
        width="stretch",
        hide_index=True
    )

    st.caption(
        "This is a provisional geometric interpretation, "
        "not independently confirmed erosion or deposition."
    )


# ==========================================
# CHANNEL MORPHOLOGY
# ==========================================

elif page == "Channel Morphology":

    st.header("Channel Morphology")

    intervals = get_intervals(channel)

    selected = st.selectbox(
        "Select observation period",
        intervals,
        format_func=interval_label
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
        width="stretch",
        hide_index=True
    )

    st.divider()

    st.subheader("Widening and Narrowing")

    counts = (
        selected_data["condition"]
        .value_counts()
        .rename_axis("Condition")
        .reset_index(name="Transect Count")
    )

    st.bar_chart(
        counts,
        x="Condition",
        y="Transect Count"
    )


# ==========================================
# SPATIAL ANALYSIS
# ==========================================

elif page == "Spatial Analysis":

    st.header("Spatial Migration Distribution")

    intervals = get_intervals(migration)

    selected = st.selectbox(
        "Select period",
        intervals,
        format_func=interval_label
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

    spatial_data = transects.merge(
        selected_data,
        on="transect_id"
    )

    spatial_data = gpd.GeoDataFrame(
        spatial_data,
        geometry="geometry",
        crs=transects.crs
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
        f"{bank.title()} Bank: {interval_label(selected)}"
    )

    ax.set_aspect("equal")
    ax.set_axis_off()

    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "Colours represent signed along-transect "
        "migration rates, not independently verified "
        "erosion or accretion."
    )

    st.dataframe(
        selected_data,
        width="stretch",
        hide_index=True
    )


# ==========================================
# TRANSECT EXPLORER
# ==========================================

elif page == "Transect Explorer":

    st.header("Individual Transect Explorer")

    transect_ids = sorted(
        channel["transect_id"].unique()
    )

    selected_transect = st.selectbox(
        "Choose a transect",
        transect_ids
    )

    transect_data = channel[
        channel["transect_id"] == selected_transect
    ].copy()

    transect_data["period"] = (
        transect_data["start_year"].astype(str)
        + "–"
        + transect_data["end_year"].astype(str)
    )

    st.subheader(f"Transect {selected_transect}")

    col1, col2 = st.columns(2)

    col1.metric(
        "Average Width Change",
        f"{transect_data['width_change_m'].mean():.2f} m"
    )

    col2.metric(
        "Average Centre Shift",
        f"{transect_data['centre_shift_m'].mean():.2f} m"
    )

    st.subheader("Width Change Through Time")

    st.line_chart(
        transect_data,
        x="period",
        y="width_change_m"
    )

    st.subheader("Centre Shift Through Time")

    st.line_chart(
        transect_data,
        x="period",
        y="centre_shift_m"
    )

    st.subheader("Detailed Measurements")

    st.dataframe(
        transect_data,
        width="stretch",
        hide_index=True
    )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "RiverSim | Exploratory river morphology analysis "
    "| EPSG:32645"
)
