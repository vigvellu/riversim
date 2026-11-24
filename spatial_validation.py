
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from pathlib import Path

DATA_DIR = Path("data/raw")
REPORT_DIR = Path("outputs/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load datasets
points = gpd.read_file(DATA_DIR / "bank_points.gpkg")
banklines = gpd.read_file(DATA_DIR / "banklines.gpkg")
water = gpd.read_file(DATA_DIR / "water_polygons.gpkg")

# Check coordinate reference systems
print("===== CRS CHECK =====")
print("Points:", points.crs)
print("Banklines:", banklines.crs)
print("Water:", water.crs)

if not (
    points.crs == banklines.crs == water.crs
):
    raise ValueError("CRS mismatch! Reproject before continuing.")

# Combine water polygons belonging to the same year
water_by_year = {
    year: unary_union(group.geometry.tolist())
    for year, group in water.groupby("year")
}

# Combine banklines by year and bank
lines_by_group = {
    (year, bank): unary_union(group.geometry.tolist())
    for (year, bank), group in banklines.groupby(
        ["year", "bank"]
    )
}

# Calculate spatial distances
records = []

for _, point in points.iterrows():

    year = point["year"]
    bank = point["bank"]
    geometry = point.geometry

    matching_line = lines_by_group[(year, bank)]
    matching_water = water_by_year[year]

    line_distance = geometry.distance(matching_line)

    water_boundary_distance = geometry.distance(
        matching_water.boundary
    )

    inside_water = matching_water.covers(geometry)

    records.append({
        "year": year,
        "bank": bank,
        "transect_id": point["transect_id"],
        "bankline_distance_m": line_distance,
        "water_boundary_distance_m": water_boundary_distance,
        "inside_or_on_water_polygon": inside_water
    })

validation = pd.DataFrame(records)

# Save individual point checks
validation.to_csv(
    REPORT_DIR / "spatial_validation.csv",
    index=False
)

# Summarize results
summary = validation.groupby(
    ["year", "bank"]
).agg(
    point_count=("transect_id", "count"),
    mean_bankline_distance=(
        "bankline_distance_m", "mean"
    ),
    max_bankline_distance=(
        "bankline_distance_m", "max"
    ),
    mean_water_boundary_distance=(
        "water_boundary_distance_m", "mean"
    ),
    max_water_boundary_distance=(
        "water_boundary_distance_m", "max"
    ),
    points_inside_water=(
        "inside_or_on_water_polygon", "sum"
    )
).reset_index()

print("\n===== SPATIAL VALIDATION SUMMARY =====")
print(summary.round(3).to_string(index=False))

print("\n===== POINTS FARTHEST FROM THEIR BANKLINES =====")
print(
    validation.nlargest(
        10, "bankline_distance_m"
    ).round(3).to_string(index=False)
)

print("\n===== POINTS FARTHEST FROM WATER BOUNDARIES =====")
print(
    validation.nlargest(
        10, "water_boundary_distance_m"
    ).round(3).to_string(index=False)
)

print("\n===== POINTS OUTSIDE WATER POLYGONS =====")
print(
    validation[
        ~validation["inside_or_on_water_polygon"]
    ].groupby(["year", "bank"]).size()
)

print("\nSpatial validation complete!")
print("Saved: outputs/reports/spatial_validation.csv")
