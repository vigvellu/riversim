
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

REPORT_DIR = Path("outputs/reports")
GRAPH_DIR = Path("outputs/graphs")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

print("\nRIVERSIM — CONSOLIDATED HISTORICAL CHANGE REPORT")


# ==========================================
# FILE DISCOVERY
# ==========================================

def find_file(filename):

    matches = list(Path("outputs").rglob(filename))

    if not matches:
        raise FileNotFoundError(
            f"Could not find {filename} inside outputs/"
        )

    return matches[0]


spatial_file = find_file(
    "spatial_migration_interval_summary.csv"
)

centreline_file = find_file(
    "centreline_displacement_results.csv"
)

channel_file = find_file(
    "channel_change_results.csv"
)

transect_file = find_file(
    "spatial_migration_by_transect.csv"
)


# ==========================================
# LOAD EXISTING ANALYSES
# ==========================================

spatial = pd.read_csv(spatial_file)

centreline = pd.read_csv(centreline_file)

channel_raw = pd.read_csv(channel_file)

transects = pd.read_csv(transect_file)


print("\n===== INPUT DATA =====")

for name, frame in [
    ("Spatial migration", spatial),
    ("Centreline displacement", centreline),
    ("Channel change", channel_raw),
    ("Transect migration", transects)
]:

    print(f"{name}: {len(frame)} records")


# ==========================================
# AGGREGATE CHANNEL CHANGE
# ==========================================

channel = channel_raw.groupby(
    ["start_year", "end_year"]
).agg(

    mean_width_change=(
        "width_change_m",
        "mean"
    ),

    median_width_change=(
        "width_change_m",
        "median"
    ),

    mean_width_rate=(
        "width_change_rate_m_per_year",
        "mean"
    ),

    mean_centre_shift=(
        "centre_shift_m",
        "mean"
    ),

    mean_centre_rate=(
        "centre_shift_rate_m_per_year",
        "mean"
    )

).reset_index()


print(
    f"Aggregated channel intervals: {len(channel)}"
)


# ==========================================
# VALIDATE REQUIRED FIELDS
# ==========================================

required_spatial = {
    "start_year",
    "end_year",
    "mean_displacement_m",
    "median_displacement_m",
    "mean_annual_rate",
    "southward_count",
    "northward_count",
    "stable_count"
}

required_centreline = {
    "year",
    "mean_displacement_m",
    "median_displacement_m",
    "max_displacement_m",
    "centreline_length_m"
}

required_channel = {
    "start_year",
    "end_year",
    "mean_width_change",
    "median_width_change",
    "mean_width_rate",
    "mean_centre_shift",
    "mean_centre_rate"
}

required_transects = {
    "transect_id",
    "start_year",
    "end_year",
    "displacement_m",
    "direction"
}


for name, frame, required in [
    ("Spatial migration", spatial, required_spatial),
    ("Centreline displacement", centreline, required_centreline),
    ("Channel change", channel, required_channel),
    ("Transect migration", transects, required_transects)
]:

    missing = required - set(frame.columns)

    if missing:

        raise ValueError(
            f"{name} is missing columns: {sorted(missing)}"
        )


print("\nAll required columns validated successfully.")


# ==========================================
# PREPARE HISTORICAL INTERVAL SUMMARY
# ==========================================

master = spatial.merge(
    channel,
    on=["start_year", "end_year"],
    how="outer",
    validate="one_to_one"
)

master = master.sort_values(
    ["start_year", "end_year"]
).reset_index(drop=True)


# ==========================================
# ADD INTERPRETATION LABELS
# ==========================================

master["centre_movement"] = np.select(

    [
        master["mean_displacement_m"] > 15,
        master["mean_displacement_m"] < -15
    ],

    [
        "Southward",
        "Northward"
    ],

    default="Relatively stable"
)


master["width_trend"] = np.select(

    [
        master["mean_width_change"] > 15,
        master["mean_width_change"] < -15
    ],

    [
        "Widening",
        "Narrowing"
    ],

    default="Relatively stable"
)


# ==========================================
# SAVE MASTER REPORT
# ==========================================

master.to_csv(
    REPORT_DIR / "historical_change_master.csv",
    index=False
)


# ==========================================
# CENTRELINE SUMMARY
# ==========================================

centreline = centreline.sort_values(
    "year"
).reset_index(drop=True)


centreline.to_csv(
    REPORT_DIR / "historical_centreline_summary.csv",
    index=False
)


# ==========================================
# TRANSECT SUMMARY
# ==========================================

transect_summary = transects.groupby(
    ["start_year", "end_year"]
).agg(

    transect_count=(
        "transect_id",
        "nunique"
    ),

    mean_displacement_m=(
        "displacement_m",
        "mean"
    ),

    max_southward_m=(
        "displacement_m",
        "max"
    ),

    max_northward_m=(
        "displacement_m",
        "min"
    ),

    southward_count=(
        "direction",
        lambda x: (x == "Southward").sum()
    ),

    northward_count=(
        "direction",
        lambda x: (x == "Northward").sum()
    ),

    stable_count=(
        "direction",
        lambda x: (x == "Stable").sum()
    )

).reset_index()


transect_summary.to_csv(
    REPORT_DIR / "historical_transect_summary.csv",
    index=False
)


# ==========================================
# PREPARE PERIOD LABELS
# ==========================================

periods = (
    master["start_year"].astype(int).astype(str)
    + "–"
    + master["end_year"].astype(int).astype(str)
)


# ==========================================
# GRAPH 1 — CENTRE MOVEMENT
# ==========================================

plt.figure(figsize=(11, 6))

plt.bar(
    periods,
    master["mean_displacement_m"]
)

plt.axhline(0, linewidth=1)

plt.ylabel("Mean centre displacement (m)")
plt.xlabel("Historical interval")

plt.title(
    "Historical River Centre Movement"
)

plt.grid(axis="y", alpha=0.3)

plt.xticks(rotation=20)

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "historical_centre_movement_summary.png",
    dpi=300
)

plt.close()


# ==========================================
# GRAPH 2 — CHANNEL WIDTH CHANGE
# ==========================================

plt.figure(figsize=(11, 6))

plt.bar(
    periods,
    master["mean_width_change"]
)

plt.axhline(0, linewidth=1)

plt.ylabel("Mean channel width change (m)")
plt.xlabel("Historical interval")

plt.title(
    "Historical Channel Width Change"
)

plt.grid(axis="y", alpha=0.3)

plt.xticks(rotation=20)

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "historical_channel_width_summary.png",
    dpi=300
)

plt.close()


# ==========================================
# GRAPH 3 — CENTRELINE DISPLACEMENT
# ==========================================

plt.figure(figsize=(10, 6))

plt.plot(
    centreline["year"],
    centreline["mean_displacement_m"],
    marker="o",
    linewidth=2
)

plt.xlabel("Year")

plt.ylabel(
    "Mean distance from 1990 centreline (m)"
)

plt.title(
    "Historical Centreline Displacement"
)

plt.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "historical_centreline_summary.png",
    dpi=300
)

plt.close()


# ==========================================
# GRAPH 4 — MIGRATION DIRECTION
# ==========================================

x = np.arange(len(master))

width = 0.35

plt.figure(figsize=(11, 6))

plt.bar(
    x - width / 2,
    master["southward_count"],
    width,
    label="Southward"
)

plt.bar(
    x + width / 2,
    master["northward_count"],
    width,
    label="Northward"
)

plt.xticks(
    x,
    periods,
    rotation=20
)

plt.ylabel("Number of transects")

plt.xlabel("Historical interval")

plt.title(
    "Historical Migration Direction by Transect"
)

plt.legend()

plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "historical_migration_direction_summary.png",
    dpi=300
)

plt.close()


# ==========================================
# GENERATE TEXT REPORT
# ==========================================

report_lines = [

    "RIVERSIM",

    "CONSOLIDATED HISTORICAL CHANGE REPORT",

    "Study period: 1990–2025",

    "",

    "IMPORTANT:",

    "Results are based on reconstructed and digitized GIS data.",

    "They should be treated as provisional until validated against",

    "original satellite imagery and independent reference data.",

    "",

    "HISTORICAL INTERVAL SUMMARY",

    ""
]


for _, row in master.iterrows():

    period = (
        f"{int(row['start_year'])}–"
        f"{int(row['end_year'])}"
    )

    report_lines.extend([

        f"Period: {period}",

        f"Mean centre movement: "
        f"{row['mean_displacement_m']:.2f} m",

        f"Mean width change: "
        f"{row['mean_width_change']:.2f} m",

        f"Centre direction: "
        f"{row['centre_movement']}",

        f"Channel trend: "
        f"{row['width_trend']}",

        f"Southward transects: "
        f"{int(row['southward_count'])}",

        f"Northward transects: "
        f"{int(row['northward_count'])}",

        f"Stable transects: "
        f"{int(row['stable_count'])}",

        ""
    ])


report_lines.extend([

    "CENTRELINE DISPLACEMENT FROM 1990",

    ""
])


for _, row in centreline.iterrows():

    report_lines.append(

        f"{int(row['year'])}: "
        f"{row['mean_displacement_m']:.2f} m"

    )


report_lines.extend([

    "",

    "END OF REPORT"

])


report_text = "\n".join(report_lines)


(
    REPORT_DIR / "riversim_historical_report.txt"
).write_text(

    report_text,

    encoding="utf-8"

)


# ==========================================
# TERMINAL SUMMARY
# ==========================================

print("\n===== CONSOLIDATED HISTORICAL SUMMARY =====")

print(

    master[

        [

            "start_year",

            "end_year",

            "mean_displacement_m",

            "mean_width_change",

            "centre_movement",

            "width_trend"

        ]

    ].round(2).to_string(index=False)

)


print("\n===== CENTRELINE SUMMARY =====")

print(

    centreline[

        [

            "year",

            "mean_displacement_m",

            "centreline_length_m"

        ]

    ].round(2).to_string(index=False)

)


print("\n===== TRANSECT SUMMARY =====")

print(
    transect_summary.to_string(index=False)
)


# ==========================================
# OUTPUT FILES
# ==========================================

print("\n===== FILES CREATED =====")

files = [

    REPORT_DIR / "historical_change_master.csv",

    REPORT_DIR / "historical_centreline_summary.csv",

    REPORT_DIR / "historical_transect_summary.csv",

    REPORT_DIR / "riversim_historical_report.txt",

    GRAPH_DIR / "historical_centre_movement_summary.png",

    GRAPH_DIR / "historical_channel_width_summary.png",

    GRAPH_DIR / "historical_centreline_summary.png",

    GRAPH_DIR / "historical_migration_direction_summary.png"

]


for file in files:

    print(f"- {file}")


print("\nHistorical change report completed successfully.")
