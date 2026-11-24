
import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path

# ============================================================
# RIVERSIM — CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="RiverSim | Padma River",
    page_icon="🌊",
    layout="wide"
)

ROOT = Path(".")
DATA = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "outputs" / "reports"
GRAPHS = ROOT / "outputs" / "graphs"
MAPS = ROOT / "outputs" / "maps"

st.title("🌊 RiverSim")
st.caption(
    "Interactive River Migration Analysis and Scenario Exploration "
    "| Padma River, Rajshahi, Bangladesh"
)

st.warning(
    "Research disclaimer: Results are based on prepared spatial "
    "measurements. They are exploratory and require validation "
    "against original satellite imagery and field observations."
)

# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def read_csv_file(path):
    path = Path(path)
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def read_vector_file(path):
    path = Path(path)
    if path.exists():
        return gpd.read_file(path)
    return gpd.GeoDataFrame()


@st.cache_data
def load_project_data():

    data = {
        "water": read_vector_file(DATA / "water_polygons.gpkg"),
        "bank_points": read_vector_file(DATA / "bank_points.gpkg"),
        "banklines": read_vector_file(DATA / "banklines.gpkg"),
        "transects": read_vector_file(DATA / "transects.gpkg"),
        "centrelines": read_vector_file(
            PROCESSED / "historical_centrelines.gpkg"
        ),

        "migration": read_csv_file(
            REPORTS / "migration_rates.csv"
        ),
        "nsm": read_csv_file(
            REPORTS / "nsm_epr_results.csv"
        ),
        "channel": read_csv_file(
            REPORTS / "channel_change_results.csv"
        ),
        "erosion": read_csv_file(
            REPORTS / "erosion_accretion_results.csv"
        ),
        "erosion_summary": read_csv_file(
            REPORTS / "erosion_accretion_bank_summary.csv"
        ),
        "hotspots": read_csv_file(
            REPORTS / "historical_erosion_hotspot_ranking.csv"
        ),
        "historical_master": read_csv_file(
            REPORTS / "historical_change_master.csv"
        ),
        "centreline_summary": read_csv_file(
            REPORTS / "historical_centreline_summary.csv"
        ),
        "transect_summary": read_csv_file(
            REPORTS / "historical_transect_summary.csv"
        ),
        "quality_checks": read_csv_file(
            REPORTS / "data_quality_checks.csv"
        ),
        "quality_flags": read_csv_file(
            REPORTS / "data_quality_review_register.csv"
        ),
        "migration_flags": read_csv_file(
            REPORTS / "migration_rate_review_flags.csv"
        ),
        "width_flags": read_csv_file(
            REPORTS / "channel_width_review_flags.csv"
        ),
        "centreline_quality": read_csv_file(
            REPORTS / "centreline_quality_assessment.csv"
        ),
        "centreline_segments": read_csv_file(
            REPORTS / "centreline_segment_quality.csv"
        )
    }

    return data


try:
    D = load_project_data()

except Exception as error:
    st.error(f"Could not load project data: {error}")
    st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def available(df, columns=None):
    if df is None or df.empty:
        return False

    if columns:
        return all(col in df.columns for col in columns)

    return True


def get_intervals(df):

    required = ["start_year", "end_year"]

    if not available(df, required):
        return []

    return sorted(
        df[required]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )


def interval_label(interval):
    return f"{interval[0]}–{interval[1]}"


def show_image(path, caption=None):

    path = Path(path)

    if path.exists():
        st.image(str(path), caption=caption, width="stretch")
    else:
        st.info(f"Image not available yet: {path}")


def show_table(df):

    if df is not None and not df.empty:
        st.dataframe(
            df,
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No data available for this section.")


def download_csv(df, filename, label="Download CSV"):

    if df is not None and not df.empty:

        st.download_button(
            label=label,
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=filename,
            mime="text/csv"
        )


def get_file_count(folder, suffix=None):

    folder = Path(folder)

    if not folder.exists():
        return 0

    files = list(folder.rglob("*"))

    if suffix:
        return sum(
            1 for file in files
            if file.is_file() and file.suffix.lower() == suffix.lower()
        )

    return sum(1 for file in files if file.is_file())


def show_metric_row(items):

    cols = st.columns(len(items))

    for col, (label, value, help_text) in zip(cols, items):

        col.metric(
            label,
            value,
            help=help_text
        )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🌊 RiverSim")

st.sidebar.caption("Padma River Research Dashboard")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Bank Migration",
        "Erosion & Accretion",
        "Channel Morphology",
        "Spatial Analysis",
        "Transect Explorer",
        "Historical Hotspots",
        "Data Quality",
        "Historical Reports",
        "Download Centre"
    ]
)

st.sidebar.divider()

st.sidebar.caption("Project information")

st.sidebar.write("Study period: 1990–2025")
st.sidebar.write("Observation years: 6")
st.sidebar.write("Transects: 19")
st.sidebar.write("Coordinate system: EPSG:32645")

st.sidebar.divider()

st.sidebar.caption(
    "RiverSim is an exploratory academic project, "
    "not a calibrated predictive river model."
)


# ============================================================
# PAGE 1 — OVERVIEW
# ============================================================

if page == "Overview":

    st.header("Project Overview")

    water = D["water"]
    migration = D["migration"]
    nsm = D["nsm"]
    transects = D["transects"]

    if water.empty:
        st.error("Water polygon data is missing.")
        st.stop()

    total_area = (
        water.groupby("year")["area_km2"]
        .sum()
        .sort_index()
    )

    latest_area = total_area.iloc[-1]

    years = sorted(water["year"].unique())

    mean_north = None
    mean_south = None

    if available(nsm, ["bank", "NSM_m"]):

        mean_north = nsm[
            nsm["bank"] == "north"
        ]["NSM_m"].mean()

        mean_south = nsm[
            nsm["bank"] == "south"
        ]["NSM_m"].mean()

    show_metric_row([
        ("Observation Years", str(len(years)), None),
        ("Transects", str(len(transects)), None),
        ("Latest Water Area", f"{latest_area:.2f} km²", None),
        ("Study Duration", "35 years", None)
    ])

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

    if mean_north is not None and mean_south is not None:

        st.subheader("Long-term Bank Displacement")

        show_metric_row([
            ("North Bank Mean NSM", f"{mean_north:.2f} m", None),
            ("South Bank Mean NSM", f"{mean_south:.2f} m", None)
        ])

    st.divider()

    st.subheader("Historical River Configuration")

    show_image(
        MAPS / "historical_all_years_overlay.png",
        "Historical overlay of banklines, water boundaries and reconstructed centrelines"
    )

    st.subheader("Dataset Inventory")

    inventory = pd.DataFrame({
        "Dataset": [
            "Bank points",
            "Banklines",
            "Transects",
            "Water polygons",
            "Historical centrelines",
            "Migration records",
            "Channel change records",
            "Erosion/accretion records"
        ],
        "Records": [
            len(D["bank_points"]),
            len(D["banklines"]),
            len(D["transects"]),
            len(D["water"]),
            len(D["centrelines"]),
            len(D["migration"]),
            len(D["channel"]),
            len(D["erosion"])
        ]
    })

    show_table(inventory)


# ============================================================
# PAGE 2 — BANK MIGRATION
# ============================================================

elif page == "Bank Migration":

    st.header("Bank Migration Analysis")

    migration = D["migration"]

    if not available(
        migration,
        [
            "start_year",
            "end_year",
            "bank",
            "transect_id",
            "migration_rate_m_per_year"
        ]
    ):
        st.error("Migration data is unavailable or incomplete.")
        st.stop()

    intervals = get_intervals(migration)

    selected = st.selectbox(
        "Observation period",
        intervals,
        format_func=interval_label
    )

    bank = st.selectbox(
        "Bank",
        ["north", "south"]
    )

    selected_data = migration[
        (migration["start_year"] == selected[0]) &
        (migration["end_year"] == selected[1]) &
        (migration["bank"] == bank)
    ].sort_values("transect_id")

    if selected_data.empty:
        st.warning("No records found.")
        st.stop()

    show_metric_row([
        (
            "Mean Migration Rate",
            f"{selected_data['migration_rate_m_per_year'].mean():.2f} m/year",
            None
        ),
        (
            "Maximum Rate",
            f"{selected_data['migration_rate_m_per_year'].max():.2f} m/year",
            None
        ),
        (
            "Minimum Rate",
            f"{selected_data['migration_rate_m_per_year'].min():.2f} m/year",
            None
        )
    ])

    st.subheader("Migration Rate by Transect")

    st.bar_chart(
        selected_data,
        x="transect_id",
        y="migration_rate_m_per_year"
    )

    st.subheader("Measurement Records")

    show_table(selected_data)

    download_csv(
        selected_data,
        "river_migration_selected_period.csv"
    )

    st.caption(
        "Rates represent signed displacement along transects. "
        "Positive and negative values do not automatically "
        "mean erosion or accretion on both banks."
    )


# ============================================================
# PAGE 3 — EROSION AND ACCRETION
# ============================================================

elif page == "Erosion & Accretion":

    st.header("Provisional Erosion & Accretion")

    st.info(
        "Positive landward rates indicate retreat, while negative "
        "landward rates indicate advance. The conversion from "
        "transect displacement depends on bank orientation."
    )

    migration = D["migration"]

    intervals = get_intervals(migration)

    selected = st.selectbox(
        "Observation period",
        intervals,
        format_func=interval_label
    )

    bank = st.selectbox(
        "Bank",
        ["north", "south"]
    )

    selected_data = migration[
        (migration["start_year"] == selected[0]) &
        (migration["end_year"] == selected[1]) &
        (migration["bank"] == bank)
    ].copy()

    if bank == "north":
        selected_data["landward_rate"] = (
            -selected_data["migration_rate_m_per_year"]
        )
    else:
        selected_data["landward_rate"] = (
            selected_data["migration_rate_m_per_year"]
        )

    selected_data["interpretation"] = selected_data[
        "landward_rate"
    ].apply(
        lambda value:
        "Retreat" if value > 0
        else "Advance" if value < 0
        else "Stable"
    )

    show_metric_row([
        (
            "Mean Landward Rate",
            f"{selected_data['landward_rate'].mean():.2f} m/year",
            None
        ),
        (
            "Retreat Transects",
            str((selected_data["interpretation"] == "Retreat").sum()),
            None
        ),
        (
            "Advance Transects",
            str((selected_data["interpretation"] == "Advance").sum()),
            None
        )
    ])

    st.subheader("Retreat and Advance by Transect")

    st.bar_chart(
        selected_data,
        x="transect_id",
        y="landward_rate"
    )

    st.subheader("Classification")

    show_table(
        selected_data[
            [
                "transect_id",
                "migration_rate_m_per_year",
                "landward_rate",
                "interpretation"
            ]
        ]
    )

    st.caption(
        "This is a provisional geometric interpretation, "
        "not independently confirmed erosion or deposition."
    )


# ============================================================
# PAGE 4 — CHANNEL MORPHOLOGY
# ============================================================

elif page == "Channel Morphology":

    st.header("Channel Morphology")

    channel = D["channel"]

    if not available(
        channel,
        [
            "start_year",
            "end_year",
            "transect_id",
            "width_change_m",
            "width_change_rate_m_per_year",
            "centre_shift_m",
            "condition"
        ]
    ):
        st.error("Channel morphology data is unavailable.")
        st.stop()

    intervals = get_intervals(channel)

    selected = st.selectbox(
        "Observation period",
        intervals,
        format_func=interval_label
    )

    selected_data = channel[
        (channel["start_year"] == selected[0]) &
        (channel["end_year"] == selected[1])
    ]

    show_metric_row([
        (
            "Mean Width Change",
            f"{selected_data['width_change_m'].mean():.2f} m",
            None
        ),
        (
            "Mean Width Change Rate",
            f"{selected_data['width_change_rate_m_per_year'].mean():.2f} m/year",
            None
        ),
        (
            "Mean Centre Shift",
            f"{selected_data['centre_shift_m'].mean():.2f} m",
            None
        )
    ])

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

    st.subheader("Detailed Measurements")

    show_table(selected_data)

    download_csv(
        selected_data,
        "river_channel_change_selected_period.csv"
    )


# ============================================================
# PAGE 5 — SPATIAL ANALYSIS
# ============================================================

elif page == "Spatial Analysis":

    st.header("Spatial Migration Distribution")

    migration = D["migration"]
    transects = D["transects"]

    intervals = get_intervals(migration)

    selected = st.selectbox(
        "Observation period",
        intervals,
        format_func=interval_label
    )

    bank = st.selectbox(
        "Bank",
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

    fig, ax = plt.subplots(figsize=(11, 8))

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
        f"{bank.title()} Bank — {interval_label(selected)}"
    )

    ax.set_aspect("equal")
    ax.set_axis_off()

    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "Colours represent signed along-transect migration rates."
    )

    show_table(selected_data)


# ============================================================
# PAGE 6 — TRANSECT EXPLORER
# ============================================================

elif page == "Transect Explorer":

    st.header("Individual Transect Explorer")

    channel = D["channel"]

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

    show_metric_row([
        (
            "Average Width Change",
            f"{transect_data['width_change_m'].mean():.2f} m",
            None
        ),
        (
            "Average Centre Shift",
            f"{transect_data['centre_shift_m'].mean():.2f} m",
            None
        )
    ])

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

    show_table(transect_data)


# ============================================================
# PAGE 7 — HISTORICAL HOTSPOTS
# ============================================================

elif page == "Historical Hotspots":

    st.header("Historical Erosion Hotspots")

    st.caption(
        "Net erosion/accretion classifications for 1990–2025, "
        "plotted at the corresponding 2025 bank-point positions."
    )

    show_image(
        MAPS / "historical_erosion_hotspot_map.png",
        "Historical erosion and accretion hotspot distribution"
    )

    hotspots = D["hotspots"]

    if not hotspots.empty:

        st.subheader("Erosion Hotspot Ranking")

        show_table(hotspots)

        download_csv(
            hotspots,
            "historical_erosion_hotspot_ranking.csv"
        )

    else:
        st.warning(
            "Hotspot ranking file not found. "
            "Run erosion_hotspot_map.py first."
        )

    erosion = D["erosion_summary"]

    if not erosion.empty:

        st.divider()

        st.subheader("Bank-wise Erosion and Accretion Summary")

        show_table(erosion)

    st.info(
        "Hotspot locations are based on net historical displacement. "
        "They do not represent a continuous record of where erosion "
        "occurred during the entire 35-year period."
    )


# ============================================================
# PAGE 8 — DATA QUALITY
# ============================================================

elif page == "Data Quality":

    st.header("Data Quality & Uncertainty Assessment")

    st.caption(
        "Internal spatial consistency, measurement precision "
        "and review flags."
    )

    checks = D["quality_checks"]
    flags = D["quality_flags"]

    if checks.empty:
        st.warning(
            "Quality assessment files are unavailable. "
            "Run data_quality_assessment.py first."
        )

    else:

        pass_count = 0
        review_count = 0

        if "status" in checks.columns:

            pass_count = (
                checks["status"].astype(str).str.upper() == "PASS"
            ).sum()

            review_count = (
                checks["status"].astype(str).str.upper() == "REVIEW"
            ).sum()

        show_metric_row([
            ("Quality Checks", str(len(checks)), None),
            ("Passed Checks", str(pass_count), None),
            ("Review Flags", str(review_count), None)
        ])

        st.subheader("Quality Check Register")

        show_table(checks)

        download_csv(
            checks,
            "riversim_data_quality_checks.csv"
        )

    if not flags.empty:

        st.divider()

        st.subheader("Review Register")

        show_table(flags)

        download_csv(
            flags,
            "riversim_data_quality_review_register.csv"
        )

    st.divider()

    st.subheader("Migration Rate Review")

    migration_flags = D["migration_flags"]

    if not migration_flags.empty:
        st.write(
            f"Records requiring review: {len(migration_flags)}"
        )
        show_table(migration_flags)
    else:
        st.info("Migration review file unavailable.")

    st.divider()

    st.subheader("Channel Width Review")

    width_flags = D["width_flags"]

    if not width_flags.empty:
        st.write(
            f"Records requiring review: {len(width_flags)}"
        )
        show_table(width_flags)
    else:
        st.info("Channel width review file unavailable.")

    st.divider()

    st.subheader("Centreline Quality")

    centreline_quality = D["centreline_quality"]

    if not centreline_quality.empty:
        show_table(centreline_quality)

    show_image(
        GRAPHS / "centreline_segment_quality.png",
        "Reconstructed centreline segment quality"
    )

    show_image(
        GRAPHS / "water_boundary_distance_quality.png",
        "Bank point distances from water boundaries"
    )

    st.subheader("Important Uncertainty Notes")

    st.markdown("""
    - Very small point-to-transect offsets demonstrate internal
      geometric consistency, not original measurement accuracy.
    - Observed measurement increments are relatively coarse.
    - Large migration rates and channel-width changes need
      comparison with original satellite imagery.
    - Reconstructed centrelines connect transect midpoints and
      are not independently extracted river centrelines.
    - Scenario outputs are exploratory extrapolations, not
      physically calibrated predictions.
    """)


# ============================================================
# PAGE 9 — HISTORICAL REPORTS
# ============================================================

elif page == "Historical Reports":

    st.header("Consolidated Historical Change Report")

    master = D["historical_master"]
    centreline = D["centreline_summary"]
    transect_summary = D["transect_summary"]

    if master.empty:

        st.warning(
            "Historical report files are unavailable. "
            "Run historical_change_report.py first."
        )

    else:

        st.subheader("Historical Change by Period")

        show_table(master)

        download_csv(
            master,
            "historical_change_master.csv"
        )

    st.divider()

    st.subheader("Centreline Summary")

    if not centreline.empty:
        show_table(centreline)

    else:
        st.info("Centreline summary unavailable.")

    show_image(
        GRAPHS / "historical_centre_movement_summary.png",
        "Historical centre movement"
    )

    show_image(
        GRAPHS / "historical_channel_width_summary.png",
        "Historical channel width change"
    )

    show_image(
        GRAPHS / "historical_centreline_summary.png",
        "Historical centreline summary"
    )

    show_image(
        GRAPHS / "historical_migration_direction_summary.png",
        "Historical migration direction"
    )

    st.divider()

    st.subheader("Transect-level Historical Summary")

    if not transect_summary.empty:
        show_table(transect_summary)

        download_csv(
            transect_summary,
            "historical_transect_summary.csv"
        )

    st.divider()

    st.subheader("Additional Historical Maps")

    show_image(
        MAPS / "historical_spatial_change.png",
        "Historical spatial change by observation year"
    )

    show_image(
        MAPS / "historical_all_years_overlay.png",
        "All observation years overlaid"
    )


# ============================================================
# PAGE 10 — DOWNLOAD CENTRE
# ============================================================

elif page == "Download Centre":

    st.header("RiverSim Download Centre")

    st.caption(
        "Download generated reports and analysis datasets."
    )

    folders = {
        "Reports": REPORTS,
        "Graphs": GRAPHS,
        "Maps": MAPS
    }

    st.subheader("Output Inventory")

    inventory = []

    for name, folder in folders.items():

        inventory.append({
            "Category": name,
            "Files available": get_file_count(folder)
        })

    show_table(pd.DataFrame(inventory))

    st.divider()

    st.subheader("Download Reports")

    report_files = sorted(REPORTS.glob("*"))

    for file in report_files:

        if file.is_file() and file.suffix.lower() == ".csv":

            try:
                file_data = file.read_bytes()

                st.download_button(
                    label=f"Download {file.name}",
                    data=file_data,
                    file_name=file.name,
                    mime="text/csv",
                    key=f"download_{file.name}"
                )

            except Exception as error:
                st.error(f"Could not load {file.name}: {error}")

        elif file.is_file() and file.suffix.lower() == ".txt":

            try:
                file_data = file.read_bytes()

                st.download_button(
                    label=f"Download {file.name}",
                    data=file_data,
                    file_name=file.name,
                    mime="text/plain",
                    key=f"download_{file.name}"
                )

            except Exception as error:
                st.error(f"Could not load {file.name}: {error}")

    st.divider()

    st.subheader("Generated Graphs")

    graph_files = sorted(GRAPHS.glob("*.png"))

    if graph_files:

        for file in graph_files:

            with st.expander(file.name):

                st.image(str(file), width="stretch")

                st.download_button(
                    label="Download image",
                    data=file.read_bytes(),
                    file_name=file.name,
                    mime="image/png",
                    key=f"graph_{file.name}"
                )

    else:
        st.info("No graph images found.")

    st.divider()

    st.subheader("Generated Maps")

    map_files = sorted(MAPS.glob("*.png"))

    if map_files:

        for file in map_files:

            with st.expander(file.name):

                st.image(str(file), width="stretch")

                st.download_button(
                    label="Download map",
                    data=file.read_bytes(),
                    file_name=file.name,
                    mime="image/png",
                    key=f"map_{file.name}"
                )

    else:
        st.info("No map images found.")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "RiverSim | Padma River, Rajshahi | 1990–2025 "
    "| Coordinate Reference System: EPSG:32645"
)

st.caption(
    "Exploratory spatial analysis. Findings require "
    "independent validation before scientific or engineering use."
)
