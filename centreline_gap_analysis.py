
import geopandas as gpd
import pandas as pd

from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

INPUT = Path("data/processed/historical_centre_points.gpkg")
OUTPUT = Path("outputs/reports")

OUTPUT.mkdir(parents=True, exist_ok=True)

print("\nRIVERSIM — CENTRELINE GAP ANALYSIS")


# ==========================================
# LOAD CENTRELINE POINTS
# ==========================================

points = gpd.read_file(INPUT)

points = points.sort_values(
    ["year", "chainage_m"]
)


# ==========================================
# CALCULATE CONSECUTIVE POINT DISTANCES
# ==========================================

records = []

for year, group in points.groupby("year"):

    group = group.sort_values("chainage_m")

    rows = list(group.iterrows())

    for i in range(len(rows) - 1):

        point_a = rows[i][1]
        point_b = rows[i + 1][1]

        distance = point_a.geometry.distance(
            point_b.geometry
        )

        chainage_gap = (
            point_b["chainage_m"]
            - point_a["chainage_m"]
        )

        records.append({

            "year": int(year),

            "from_transect": point_a["transect_id"],

            "to_transect": point_b["transect_id"],

            "from_chainage": point_a["chainage_m"],

            "to_chainage": point_b["chainage_m"],

            "chainage_gap_m": chainage_gap,

            "centreline_segment_m": distance,

            "extra_distance_m": distance - chainage_gap

        })


gaps = pd.DataFrame(records)


# ==========================================
# DISPLAY LARGEST SEGMENTS
# ==========================================

print("\n===== LARGEST CENTRELINE SEGMENTS =====")

largest = gaps.sort_values(
    "centreline_segment_m",
    ascending=False
)

print(
    largest.head(15).round(2).to_string(index=False)
)


# ==========================================
# FLAG UNUSUAL SEGMENTS
# ==========================================

print("\n===== SEGMENTS ABOVE 300 METRES =====")

unusual = gaps[
    gaps["centreline_segment_m"] > 300
].sort_values(
    ["year", "centreline_segment_m"],
    ascending=[True, False]
)

if unusual.empty:

    print("No segments above 300 metres.")

else:

    print(
        unusual.round(2).to_string(index=False)
    )


# ==========================================
# YEARLY GAP SUMMARY
# ==========================================

summary = (
    gaps.groupby("year")
    .agg(
        mean_segment=("centreline_segment_m", "mean"),
        median_segment=("centreline_segment_m", "median"),
        maximum_segment=("centreline_segment_m", "max"),
        segments_above_300=(
            "centreline_segment_m",
            lambda x: (x > 300).sum()
        )
    )
    .reset_index()
)

print("\n===== YEARLY GAP SUMMARY =====")

print(
    summary.round(2).to_string(index=False)
)


# ==========================================
# EXPORT
# ==========================================

gaps.to_csv(
    OUTPUT / "centreline_segment_gaps.csv",
    index=False
)

unusual.to_csv(
    OUTPUT / "unusual_centreline_segments.csv",
    index=False
)

print("\nOUTPUTS CREATED")

print("outputs/reports/centreline_segment_gaps.csv")

print("outputs/reports/unusual_centreline_segments.csv")

print("\nAnalysis completed successfully.")
