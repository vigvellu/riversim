
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from shapely.ops import unary_union

# ==========================================
# CONFIGURATION
# ==========================================

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

REPORTS = Path("outputs/reports")
GRAPHS = Path("outputs/graphs")

REPORTS.mkdir(parents=True, exist_ok=True)
GRAPHS.mkdir(parents=True, exist_ok=True)

YEARS = [1990, 2000, 2010, 2015, 2020, 2025]

# Screening thresholds, not scientific error limits.
HIGH_MIGRATION_RATE = 100
LARGE_WIDTH_CHANGE = 1000
CENTRELINE_SEGMENT_FACTOR = 2.0

print("\nRIVERSIM — DATA QUALITY & UNCERTAINTY ASSESSMENT")


# ==========================================
# LOAD DATA
# ==========================================

bank_points = gpd.read_file(
    RAW / "bank_points.gpkg"
)

banklines = gpd.read_file(
    RAW / "banklines.gpkg"
)

transects = gpd.read_file(
    RAW / "transects.gpkg"
)

water = gpd.read_file(
    RAW / "water_polygons.gpkg"
)

centrelines = gpd.read_file(
    PROCESSED / "historical_centrelines.gpkg"
)

migration = pd.read_csv(
    REPORTS / "migration_rates.csv"
)

channel = pd.read_csv(
    REPORTS / "channel_change_results.csv"
)

erosion = pd.read_csv(
    REPORTS / "erosion_accretion_results.csv"
)

print("\n===== DATA INVENTORY =====")

datasets = {
    "Bank points": bank_points,
    "Banklines": banklines,
    "Transects": transects,
    "Water polygons": water,
    "Centrelines": centrelines
}

for name, frame in datasets.items():
    print(
        f"{name}: {len(frame)} features | CRS: {frame.crs}"
    )

print("Migration records:", len(migration))
print("Channel records:", len(channel))
print("Erosion records:", len(erosion))


# ==========================================
# GENERAL VALIDATION
# ==========================================

quality_checks = []
issues = []


def add_check(
    category,
    dataset,
    check,
    value,
    status,
    explanation
):

    quality_checks.append({

        "category": category,
        "dataset": dataset,
        "check": check,
        "result": value,
        "status": status,
        "explanation": explanation

    })


def add_issue(
    category,
    location,
    description,
    severity="Review"
):

    issues.append({

        "category": category,
        "location": str(location),
        "description": description,
        "severity": severity

    })


# CRS consistency
crs_values = {
    str(frame.crs)
    for frame in datasets.values()
}

crs_ok = len(crs_values) == 1 and "EPSG:32645" in crs_values

add_check(
    "Spatial",
    "All GIS datasets",
    "CRS consistency",
    ", ".join(sorted(crs_values)),
    "PASS" if crs_ok else "REVIEW",
    "All datasets should use the same projected CRS."
)

if not crs_ok:
    add_issue(
        "Spatial",
        "All GIS datasets",
        "CRS mismatch detected.",
        "High"
    )


# Geometry validation
for name, frame in datasets.items():

    missing_geometry = int(
        frame.geometry.isna().sum()
    )

    invalid_geometry = int(
        (~frame.geometry.is_valid).sum()
    )

    add_check(
        "Geometry",
        name,
        "Missing geometries",
        missing_geometry,
        "PASS" if missing_geometry == 0 else "FAIL",
        "Number of features without geometry."
    )

    add_check(
        "Geometry",
        name,
        "Invalid geometries",
        invalid_geometry,
        "PASS" if invalid_geometry == 0 else "REVIEW",
        "Number of geometries failing validity checks."
    )

    if missing_geometry:
        add_issue(
            "Geometry",
            name,
            f"{missing_geometry} missing geometries.",
            "High"
        )

    if invalid_geometry:
        add_issue(
            "Geometry",
            name,
            f"{invalid_geometry} invalid geometries.",
            "High"
        )


# ==========================================
# RECORD COMPLETENESS
# ==========================================

expected_points = 6 * 19 * 2

add_check(
    "Completeness",
    "Bank points",
    "Expected feature count",
    f"{len(bank_points)} / {expected_points}",
    "PASS" if len(bank_points) == expected_points else "REVIEW",
    "Expected 6 years × 19 transects × 2 banks."
)

duplicate_points = int(
    bank_points.duplicated(
        ["year", "transect_id", "bank"]
    ).sum()
)

add_check(
    "Completeness",
    "Bank points",
    "Duplicate survey records",
    duplicate_points,
    "PASS" if duplicate_points == 0 else "FAIL",
    "Each transect, bank and year should have one record."
)

if duplicate_points:
    add_issue(
        "Completeness",
        "Bank points",
        f"{duplicate_points} duplicate survey records.",
        "High"
    )


# ==========================================
# MEASUREMENT PRECISION
# ==========================================

distance_values = (
    bank_points["distance_m"]
    .dropna()
    .astype(float)
)

unique_distances = np.sort(
    distance_values.unique()
)

increments = np.diff(unique_distances)

increments = increments[
    increments > 0
]

if len(increments):

    median_increment = float(
        np.median(increments)
    )

    minimum_increment = float(
        np.min(increments)
    )

    maximum_increment = float(
        np.max(increments)
    )

else:

    median_increment = np.nan
    minimum_increment = np.nan
    maximum_increment = np.nan


add_check(
    "Measurement",
    "Bank points",
    "Median observed distance increment",
    median_increment,
    "INFO",
    "Describes spacing between unique recorded values, not measurement accuracy."
)

add_check(
    "Measurement",
    "Bank points",
    "Minimum observed distance increment",
    minimum_increment,
    "INFO",
    "Smallest positive difference between unique distance values."
)

add_check(
    "Measurement",
    "Bank points",
    "Maximum observed distance increment",
    maximum_increment,
    "INFO",
    "Largest positive difference between unique distance values."
)


# ==========================================
# BANK POINT TO TRANSECT DISTANCE
# ==========================================

transect_lookup = {
    row["transect_id"]: row.geometry
    for _, row in transects.iterrows()
}

transect_distances = []

for _, row in bank_points.iterrows():

    transect = transect_lookup.get(
        row["transect_id"]
    )

    if transect is None:
        distance = np.nan
    else:
        distance = row.geometry.distance(
            transect
        )

    transect_distances.append({

        "year": row["year"],
        "transect_id": row["transect_id"],
        "bank": row["bank"],
        "distance_to_transect_m": distance

    })


transect_distance_df = pd.DataFrame(
    transect_distances
)

max_transect_offset = (
    transect_distance_df[
        "distance_to_transect_m"
    ].max()
)

mean_transect_offset = (
    transect_distance_df[
        "distance_to_transect_m"
    ].mean()
)

add_check(
    "Spatial",
    "Bank points",
    "Maximum offset from transect",
    round(max_transect_offset, 6),
    "PASS" if max_transect_offset < 1 else "REVIEW",
    "Measures how closely bank points follow their corresponding transects."
)

add_check(
    "Spatial",
    "Bank points",
    "Mean offset from transect",
    round(mean_transect_offset, 6),
    "INFO",
    "Mean geometric distance between bank points and their transects."
)


# ==========================================
# BANK POINT TO BANKLINE DISTANCE
# ==========================================

bankline_lookup = {}

for _, row in banklines.iterrows():

    bankline_lookup[
        (row["year"], row["bank"])
    ] = row.geometry


bankline_distances = []

for _, row in bank_points.iterrows():

    line = bankline_lookup.get(
        (row["year"], row["bank"])
    )

    if line is None:
        distance = np.nan
    else:
        distance = row.geometry.distance(line)

    bankline_distances.append({

        "year": row["year"],
        "transect_id": row["transect_id"],
        "bank": row["bank"],
        "distance_to_bankline_m": distance

    })


bankline_distance_df = pd.DataFrame(
    bankline_distances
)

max_bankline_offset = (
    bankline_distance_df[
        "distance_to_bankline_m"
    ].max()
)

add_check(
    "Spatial",
    "Bank points",
    "Maximum offset from bankline",
    round(max_bankline_offset, 6),
    "PASS" if max_bankline_offset < 1 else "REVIEW",
    "Checks whether measured bank points lie on their corresponding banklines."
)


# ==========================================
# WATER BOUNDARY DISTANCE
# ==========================================

water_lookup = {}

for year, group in water.groupby("year"):

    water_lookup[int(year)] = unary_union(
        group.geometry.tolist()
    )


water_distances = []

for _, row in bank_points.iterrows():

    polygon = water_lookup.get(
        int(row["year"])
    )

    if polygon is None:
        continue

    distance = row.geometry.distance(
        polygon.boundary
    )

    water_distances.append({

        "year": row["year"],
        "transect_id": row["transect_id"],
        "bank": row["bank"],
        "boundary_distance_m": distance

    })


water_distance_df = pd.DataFrame(
    water_distances
)

water_distance_df.to_csv(
    REPORTS / "water_boundary_distance_quality.csv",
    index=False
)

water_summary = water_distance_df.groupby(
    ["year", "bank"]
).agg(

    mean_boundary_distance_m=(
        "boundary_distance_m",
        "mean"
    ),

    max_boundary_distance_m=(
        "boundary_distance_m",
        "max"
    )

).reset_index()

water_summary.to_csv(
    REPORTS / "water_boundary_quality_summary.csv",
    index=False
)


# ==========================================
# HISTORICAL MIGRATION RATE FLAGS
# ==========================================

migration["absolute_rate"] = (
    migration["migration_rate_m_per_year"].abs()
)

migration["quality_flag"] = np.where(
    migration["absolute_rate"] > HIGH_MIGRATION_RATE,
    "High rate — inspect imagery",
    "No threshold flag"
)

high_rates = migration[
    migration["absolute_rate"] > HIGH_MIGRATION_RATE
].copy()

high_rates.to_csv(
    REPORTS / "migration_rate_review_flags.csv",
    index=False
)

for _, row in high_rates.iterrows():

    add_issue(
        "Migration",
        f"{row['transect_id']} {row['bank']} "
        f"{row['start_year']}-{row['end_year']}",
        f"Migration rate {row['migration_rate_m_per_year']:.2f} m/year exceeds the screening threshold.",
        "Review"
    )

add_check(
    "Migration",
    "Migration rates",
    "Rates exceeding screening threshold",
    len(high_rates),
    "REVIEW" if len(high_rates) else "PASS",
    f"Threshold: absolute rate greater than {HIGH_MIGRATION_RATE} m/year."
)


# ==========================================
# CHANNEL WIDTH CHANGE FLAGS
# ==========================================

channel["absolute_width_change"] = (
    channel["width_change_m"].abs()
)

channel["quality_flag"] = np.where(
    channel["absolute_width_change"] > LARGE_WIDTH_CHANGE,
    "Large width change — inspect imagery",
    "No threshold flag"
)

large_width_changes = channel[
    channel["absolute_width_change"] > LARGE_WIDTH_CHANGE
].copy()

large_width_changes.to_csv(
    REPORTS / "channel_width_review_flags.csv",
    index=False
)

for _, row in large_width_changes.iterrows():

    add_issue(
        "Channel morphology",
        f"{row['transect_id']} "
        f"{row['start_year']}-{row['end_year']}",
        f"Width change of {row['width_change_m']:.2f} m exceeds the screening threshold.",
        "Review"
    )

add_check(
    "Channel morphology",
    "Channel change",
    "Large width changes",
    len(large_width_changes),
    "REVIEW" if len(large_width_changes) else "PASS",
    f"Threshold: absolute width change greater than {LARGE_WIDTH_CHANGE} m."
)


# ==========================================
# CENTRELINE SEGMENT QUALITY
# ==========================================

segment_records = []

for _, row in centrelines.iterrows():

    coordinates = list(
        row.geometry.coords
    )

    lengths = []

    for i in range(len(coordinates) - 1):

        x1, y1 = coordinates[i]
        x2, y2 = coordinates[i + 1]

        segment_length = np.hypot(
            x2 - x1,
            y2 - y1
        )

        lengths.append(segment_length)

    typical_length = (
        float(np.median(lengths))
        if lengths else np.nan
    )

    for i, length in enumerate(lengths):

        ratio = (
            length / typical_length
            if typical_length > 0
            else np.nan
        )

        flagged = (
            ratio > CENTRELINE_SEGMENT_FACTOR
            if not np.isnan(ratio)
            else False
        )

        segment_records.append({

            "year": row["year"],
            "segment_number": i + 1,
            "segment_length_m": length,
            "median_segment_length_m": typical_length,
            "length_ratio": ratio,
            "quality_flag": (
                "Review" if flagged else "No threshold flag"
            )

        })

        if flagged:

            add_issue(
                "Centreline",
                f"{int(row['year'])} segment {i + 1}",
                f"Segment is {ratio:.2f} times the median segment length.",
                "Review"
            )


segment_df = pd.DataFrame(
    segment_records
)

segment_df.to_csv(
    REPORTS / "centreline_segment_quality.csv",
    index=False
)


# ==========================================
# CENTRELINE YEAR SUMMARY
# ==========================================

centreline_summary = segment_df.groupby(
    "year"
).agg(

    segment_count=(
        "segment_number",
        "count"
    ),

    mean_segment_length_m=(
        "segment_length_m",
        "mean"
    ),

    median_segment_length_m=(
        "segment_length_m",
        "median"
    ),

    maximum_segment_length_m=(
        "segment_length_m",
        "max"
    ),

    flagged_segments=(
        "quality_flag",
        lambda x: (x == "Review").sum()
    )

).reset_index()


centreline_summary.to_csv(
    REPORTS / "centreline_quality_assessment.csv",
    index=False
)


# ==========================================
# EROSION DATA CONSISTENCY
# ==========================================

erosion_sign_check = (
    ((erosion["classification"] == "Retreat") &
     (erosion["retreat_m"] <= 0))
    |
    ((erosion["classification"] == "Advance") &
     (erosion["retreat_m"] >= 0))
    |
    ((erosion["classification"] == "Stable") &
     (erosion["retreat_m"] != 0))
)

invalid_erosion_signs = int(
    erosion_sign_check.sum()
)

add_check(
    "Erosion/accretion",
    "Erosion results",
    "Classification and sign consistency",
    invalid_erosion_signs,
    "PASS" if invalid_erosion_signs == 0 else "FAIL",
    "Checks whether signed retreat values match their classifications."
)


# ==========================================
# CREATE QUALITY REGISTER
# ==========================================

quality_df = pd.DataFrame(
    quality_checks
)

quality_df.to_csv(
    REPORTS / "data_quality_checks.csv",
    index=False
)


issues_df = pd.DataFrame(
    issues,
    columns=[
        "category",
        "location",
        "description",
        "severity"
    ]
)

issues_df.to_csv(
    REPORTS / "data_quality_review_register.csv",
    index=False
)


# ==========================================
# GRAPH 1 — WATER BOUNDARY DISTANCES
# ==========================================

plt.figure(figsize=(11, 6))

for bank in ["north", "south"]:

    subset = water_summary[
        water_summary["bank"] == bank
    ]

    plt.plot(
        subset["year"],
        subset["mean_boundary_distance_m"],
        marker="o",
        label=bank.capitalize()
    )

plt.title(
    "Bank Point Distance from Water Polygon Boundary"
)

plt.xlabel("Year")
plt.ylabel("Mean distance (m)")

plt.grid(alpha=0.3)
plt.legend()

plt.tight_layout()

plt.savefig(
    GRAPHS / "water_boundary_distance_quality.png",
    dpi=300
)

plt.close()


# ==========================================
# GRAPH 2 — CENTRELINE SEGMENT LENGTHS
# ==========================================

plt.figure(figsize=(11, 6))

for year in sorted(segment_df["year"].unique()):

    subset = segment_df[
        segment_df["year"] == year
    ]

    plt.plot(
        subset["segment_number"],
        subset["segment_length_m"],
        marker="o",
        label=str(year)
    )

plt.title(
    "Historical Centreline Segment Length Assessment"
)

plt.xlabel("Segment number")
plt.ylabel("Segment length (m)")

plt.grid(alpha=0.3)
plt.legend(title="Year")

plt.tight_layout()

plt.savefig(
    GRAPHS / "centreline_segment_quality.png",
    dpi=300
)

plt.close()


# ==========================================
# GENERATE QUALITY REPORT
# ==========================================

report = [

    "RIVERSIM",

    "DATA QUALITY AND UNCERTAINTY ASSESSMENT",

    "",

    "Study period: 1990–2025",

    "Coordinate reference system: EPSG:32645",

    "",

    "IMPORTANT INTERPRETATION",

    "Screening thresholds identify records for further inspection.",

    "They do not prove that a measurement is incorrect.",

    "Observed coordinate increments do not establish positional accuracy.",

    "Original satellite imagery and independent reference data are",

    "required to quantify absolute positional uncertainty.",

    "",

    "QUALITY CHECK RESULTS",

    ""

]


for _, row in quality_df.iterrows():

    report.append(

        f"{row['category']} | {row['dataset']} | "
        f"{row['check']}: {row['result']} "
        f"[{row['status']}]"

    )


report.extend([

    "",

    "RECORDS REQUIRING REVIEW",

    ""

])


if issues_df.empty:

    report.append(
        "No review flags were generated."
    )

else:

    for _, row in issues_df.iterrows():

        report.append(

            f"{row['severity']} | "
            f"{row['category']} | "
            f"{row['location']} | "
            f"{row['description']}"

        )


report.extend([

    "",

    "CENTRELINE QUALITY SUMMARY",

    ""

])


for _, row in centreline_summary.iterrows():

    report.append(

        f"{int(row['year'])}: "
        f"{int(row['segment_count'])} segments, "
        f"median {row['median_segment_length_m']:.2f} m, "
        f"maximum {row['maximum_segment_length_m']:.2f} m, "
        f"{int(row['flagged_segments'])} flagged."

    )


report.extend([

    "",

    "END OF DATA QUALITY ASSESSMENT"

])


(REPORTS / "riversim_data_quality_report.txt").write_text(
    "\n".join(report),
    encoding="utf-8"
)


# ==========================================
# TERMINAL SUMMARY
# ==========================================

print("\n===== SPATIAL VALIDATION =====")

print(
    "Maximum point-to-transect offset:",
    round(max_transect_offset, 6),
    "m"
)

print(
    "Mean point-to-transect offset:",
    round(mean_transect_offset, 6),
    "m"
)

print(
    "Maximum point-to-bankline offset:",
    round(max_bankline_offset, 6),
    "m"
)


print("\n===== MEASUREMENT PRECISION =====")

print("Median observed increment:", median_increment)
print("Minimum observed increment:", minimum_increment)
print("Maximum observed increment:", maximum_increment)


print("\n===== REVIEW FLAGS =====")

print("High migration rates:", len(high_rates))
print("Large width changes:", len(large_width_changes))

print(
    "Unusual centreline segments:",
    int((segment_df["quality_flag"] == "Review").sum())
)


print("\n===== CENTRELINE QUALITY =====")

print(
    centreline_summary.round(2).to_string(index=False)
)


print("\n===== QUALITY CHECKS =====")

print(
    quality_df[
        ["category", "check", "result", "status"]
    ].to_string(index=False)
)


print("\n===== OUTPUT FILES =====")

output_files = [

    REPORTS / "data_quality_checks.csv",

    REPORTS / "data_quality_review_register.csv",

    REPORTS / "water_boundary_distance_quality.csv",

    REPORTS / "water_boundary_quality_summary.csv",

    REPORTS / "migration_rate_review_flags.csv",

    REPORTS / "channel_width_review_flags.csv",

    REPORTS / "centreline_segment_quality.csv",

    REPORTS / "centreline_quality_assessment.csv",

    REPORTS / "riversim_data_quality_report.txt",

    GRAPHS / "water_boundary_distance_quality.png",

    GRAPHS / "centreline_segment_quality.png"

]

for file in output_files:
    print("-", file)


print("\nStage 44 completed successfully.")
