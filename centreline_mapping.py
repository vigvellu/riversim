
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from shapely.geometry import LineString, Point

# ==========================================
# CONFIGURATION
# ==========================================

DATA = Path("data/raw")
OUTPUT = Path("outputs")

MAPS = OUTPUT / "maps"
PROCESSED = Path("data/processed")

MAPS.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

print("\nRIVERSIM — HISTORICAL CENTRELINE MAPPING")


# ==========================================
# LOAD DATA
# ==========================================

points = gpd.read_file(
    DATA / "bank_points.gpkg"
)

transects = gpd.read_file(
    DATA / "transects.gpkg"
)

if points.crs != transects.crs:
    raise ValueError("Bank points and transects have different CRS.")

print("\nCRS:", points.crs)


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

if table[
    ["north_distance", "south_distance"]
].isna().any().any():

    raise ValueError("Some transects are missing bank measurements.")


# ==========================================
# CALCULATE CHANNEL CENTRE DISTANCE
# ==========================================

table["centre_distance"] = (
    table["north_distance"]
    + table["south_distance"]
) / 2

# Previously verified geometric offset:
# projected distance = distance_m + 300

table["projected_distance"] = (
    table["centre_distance"] + 300
)


# ==========================================
# PREPARE TRANSECT GEOMETRIES
# ==========================================

transects = transects.sort_values(
    "chainage_m"
)

transect_lookup = transects.set_index(
    "transect_id"
).geometry

transect_chainage = (
    transects.set_index("transect_id")["chainage_m"]
)


# ==========================================
# GENERATE CENTRELINE POINTS
# ==========================================

point_records = []

for _, row in table.iterrows():

    transect_id = row["transect_id"]

    line = transect_lookup.loc[transect_id]

    distance = row["projected_distance"]

    if distance < 0 or distance > line.length:

        print(
            f"WARNING: {transect_id}, {row['year']} "
            "is outside its transect."
        )

        continue

    centre_point = line.interpolate(distance)

    point_records.append({

        "year": int(row["year"]),

        "transect_id": transect_id,

        "chainage_m": transect_chainage.loc[transect_id],

        "centre_distance_m": row["centre_distance"],

        "geometry": centre_point

    })


centre_points = gpd.GeoDataFrame(
    point_records,
    geometry="geometry",
    crs=transects.crs
)


# ==========================================
# GENERATE APPROXIMATE CENTRELINE GEOMETRIES
# ==========================================

line_records = []

for year in sorted(centre_points["year"].unique()):

    yearly = centre_points[
        centre_points["year"] == year
    ].sort_values("chainage_m")

    coordinates = [
        (point.x, point.y)
        for point in yearly.geometry
    ]

    if len(coordinates) < 2:

        print(f"Skipping {year}: insufficient points.")
        continue

    centreline = LineString(coordinates)

    line_records.append({

        "year": int(year),

        "point_count": len(yearly),

        "length_m": centreline.length,

        "geometry": centreline

    })


centrelines = gpd.GeoDataFrame(
    line_records,
    geometry="geometry",
    crs=transects.crs
)


# ==========================================
# PRINT SUMMARY
# ==========================================

print("\n===== CENTRELINE SUMMARY =====")

print(
    centrelines[
        ["year", "point_count", "length_m"]
    ].round(2).to_string(index=False)
)


# ==========================================
# CREATE HISTORICAL MAP
# ==========================================

fig, ax = plt.subplots(
    figsize=(12, 10)
)

for _, row in centrelines.iterrows():

    gpd.GeoSeries(
        [row.geometry],
        crs=centrelines.crs
    ).plot(
        ax=ax,
        linewidth=2,
        label=str(row["year"])
    )


ax.set_title(
    "Historical Padma River Channel Centreline\n"
    "1990–2025"
)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")

ax.set_aspect("equal")

ax.grid(
    True,
    alpha=0.3
)

ax.legend(
    title="Year"
)

plt.tight_layout()

plt.savefig(
    MAPS / "historical_centrelines.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==========================================
# EXPORT GEOPACKAGE
# ==========================================

centrelines.to_file(
    PROCESSED / "historical_centrelines.gpkg",
    layer="centrelines",
    driver="GPKG"
)

centre_points.to_file(
    PROCESSED / "historical_centre_points.gpkg",
    layer="centre_points",
    driver="GPKG"
)


# ==========================================
# EXPORT CSV
# ==========================================

csv_data = centre_points.copy()

csv_data["easting"] = csv_data.geometry.x
csv_data["northing"] = csv_data.geometry.y

csv_data.drop(
    columns="geometry"
).to_csv(
    PROCESSED / "centreline_coordinates.csv",
    index=False
)


# ==========================================
# COMPLETION
# ==========================================

print("\n===== OUTPUTS CREATED =====")

print("outputs/maps/historical_centrelines.png")

print("data/processed/historical_centrelines.gpkg")

print("data/processed/historical_centre_points.gpkg")

print("data/processed/centreline_coordinates.csv")

print("\nCentreline mapping completed successfully.")
