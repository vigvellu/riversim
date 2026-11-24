
import geopandas as gpd
import pandas as pd

from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

DATA = Path("data/raw")
OUTPUT = Path("outputs/reports")

OUTPUT.mkdir(parents=True, exist_ok=True)

SUSPICIOUS_PAIRS = [
    ("T02", "T03"),
    ("T18", "T19")
]

print("\nRIVERSIM — CENTRELINE ANOMALY INVESTIGATION")


# ==========================================
# LOAD ORIGINAL DATA
# ==========================================

points = gpd.read_file(
    DATA / "bank_points.gpkg"
)

transects = gpd.read_file(
    DATA / "transects.gpkg"
)


# ==========================================
# PREPARE BANK MEASUREMENTS
# ==========================================

table = points.pivot_table(
    index=["year", "transect_id"],
    columns="bank",
    values="distance_m"
).reset_index()

table.columns.name = None

table = table.rename(
    columns={
        "north": "north_distance",
        "south": "south_distance"
    }
)

table["channel_width"] = (
    table["south_distance"]
    - table["north_distance"]
)

table["channel_centre"] = (
    table["north_distance"]
    + table["south_distance"]
) / 2


# ==========================================
# RECONSTRUCT CENTRE POINTS
# ==========================================

transect_lookup = transects.set_index(
    "transect_id"
).geometry

records = []

for _, row in table.iterrows():

    line = transect_lookup.loc[
        row["transect_id"]
    ]

    projected_distance = (
        row["channel_centre"] + 300
    )

    if not 0 <= projected_distance <= line.length:
        continue

    centre_point = line.interpolate(
        projected_distance
    )

    records.append({

        "year": int(row["year"]),

        "transect_id": row["transect_id"],

        "north_distance": row["north_distance"],

        "south_distance": row["south_distance"],

        "channel_width": row["channel_width"],

        "channel_centre": row["channel_centre"],

        "geometry": centre_point

    })


centres = gpd.GeoDataFrame(
    records,
    geometry="geometry",
    crs=transects.crs
)


# ==========================================
# INVESTIGATE SUSPICIOUS PAIRS
# ==========================================

pair_records = []

for year in sorted(centres["year"].unique()):

    yearly = centres[
        centres["year"] == year
    ].set_index("transect_id")

    for first, second in SUSPICIOUS_PAIRS:

        a = yearly.loc[first]
        b = yearly.loc[second]

        centre_distance = (
            a.geometry.distance(b.geometry)
        )

        north_difference = (
            b["north_distance"]
            - a["north_distance"]
        )

        south_difference = (
            b["south_distance"]
            - a["south_distance"]
        )

        pair_records.append({

            "year": year,

            "pair": f"{first}-{second}",

            f"{first}_north": a["north_distance"],

            f"{second}_north": b["north_distance"],

            f"{first}_south": a["south_distance"],

            f"{second}_south": b["south_distance"],

            f"{first}_width": a["channel_width"],

            f"{second}_width": b["channel_width"],

            "north_difference": north_difference,

            "south_difference": south_difference,

            "centre_distance": centre_distance

        })


pair_results = pd.DataFrame(pair_records)


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n===== ORIGINAL BANK MEASUREMENTS =====")

for pair in pair_results["pair"].unique():

    print(f"\n--- TRANSECT PAIR: {pair} ---")

    subset = pair_results[
        pair_results["pair"] == pair
    ]

    print(
        subset.round(2).to_string(index=False)
    )


# ==========================================
# DISPLAY LARGEST CHANGES
# ==========================================

print("\n===== CENTRE DISTANCE BY YEAR =====")

comparison = pair_results.pivot(
    index="year",
    columns="pair",
    values="centre_distance"
)

print(
    comparison.round(2).to_string()
)


# ==========================================
# EXPORT
# ==========================================

pair_results.to_csv(
    OUTPUT / "centreline_anomaly_measurements.csv",
    index=False
)

comparison.to_csv(
    OUTPUT / "centreline_anomaly_comparison.csv"
)

print("\nOUTPUTS CREATED")

print(
    "outputs/reports/centreline_anomaly_measurements.csv"
)

print(
    "outputs/reports/centreline_anomaly_comparison.csv"
)

print("\nInvestigation completed successfully.")
