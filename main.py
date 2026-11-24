
import geopandas as gpd
from pathlib import Path

DATA_DIR = Path("data/raw")

points = gpd.read_file(DATA_DIR / "bank_points.gpkg")

print("=" * 45)
print("       RIVERSIM - BANK POINT ANALYSIS")
print("=" * 45)

# Number of points for each year and bank
print("\nPOINT COUNTS:")
print(points.groupby(["year", "bank"]).size())

# Number of unique transects
print("\nUNIQUE TRANSECTS:")
print(sorted(points["transect_id"].unique()))

# Check for duplicate point records
print("\nDUPLICATE RECORDS:")
print(
    points.duplicated(
        subset=["year", "bank", "transect_id"]
    ).sum()
)

# Inspect distance values
print("\nDISTANCE STATISTICS:")
print(points["distance_m"].describe())

# Inspect chainage values
print("\nCHAINAGE STATISTICS:")
print(points["chainage_m"].describe())

# Show sample records
print("\nSAMPLE DATA:")
print(points[
    ["year", "bank", "transect_id",
     "chainage_m", "distance_m"]
].head(12))

print("\nINSPECTION COMPLETE")
