
import geopandas as gpd
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")

# Load datasets
water = gpd.read_file(DATA_DIR / "water_polygons.gpkg")
banklines = gpd.read_file(DATA_DIR / "banklines.gpkg")
points = gpd.read_file(DATA_DIR / "bank_points.gpkg")

# Water area summary
water_summary = water.groupby("year").agg(
    polygon_count=("area_km2", "count"),
    total_area_km2=("area_km2", "sum"),
    mean_polygon_area_km2=("area_km2", "mean")
).reset_index()

# Bankline length summary
banklines["length_km"] = (
    banklines.geometry.length / 1000
)

length_summary = banklines.groupby(
    ["year", "bank"]
)["length_km"].sum().unstack()

# Compare reported and geometric water area
water["geometry_area_km2"] = (
    water.geometry.area / 1_000_000
)

print("\n===== WATER POLYGON SUMMARY =====")
print(water_summary.to_string(index=False))

print("\n===== REPORTED VS GEOMETRIC AREA =====")
print(
    water[[
        "year",
        "area_km2",
        "geometry_area_km2"
    ]].to_string(index=False)
)

print("\n===== BANKLINE LENGTHS (KM) =====")
print(length_summary.round(3))

print("\n===== POINT COUNTS BY YEAR =====")
print(
    points.groupby("year").size()
)

print("\nVALIDATION COMPLETE")
