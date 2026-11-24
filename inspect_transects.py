
import geopandas as gpd
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")

# Load datasets
points = gpd.read_file(DATA_DIR / "bank_points.gpkg")
transects = gpd.read_file(DATA_DIR / "transects.gpkg")

# Match each bank point to its transect
transect_lookup = transects.set_index("transect_id")

results = []

for _, point in points.iterrows():
    transect = transect_lookup.loc[point["transect_id"]].geometry

    # Position measured along the transect from its first endpoint
    projected_distance = transect.project(point.geometry)

    # How far the point is from its transect
    offset = point.geometry.distance(transect)

    results.append({
        "year": point["year"],
        "bank": point["bank"],
        "transect_id": point["transect_id"],
        "stored_distance_m": point["distance_m"],
        "projected_distance_m": projected_distance,
        "offset_from_transect_m": offset
    })

results = pd.DataFrame(results)

print("\n===== TRANSECT GEOMETRY =====")

for transect_id in ["T01", "T10", "T19"]:
    line = transect_lookup.loc[transect_id].geometry

    print(f"\n{transect_id}")
    print(f"Length: {line.length:.2f} m")
    print(f"Start: {line.coords[0]}")
    print(f"End: {line.coords[-1]}")

print("\n===== T01 BANK POINT COMPARISON =====")

print(
    results[results["transect_id"] == "T01"]
    .sort_values(["year", "bank"])
    .to_string(index=False)
)

print("\n===== POINT-TO-TRANSECT OFFSET =====")

print(results["offset_from_transect_m"].describe())

print("\n===== STORED VS PROJECTED DISTANCE =====")

results["difference_m"] = (
    results["stored_distance_m"]
    - results["projected_distance_m"]
)

print(results["difference_m"].describe())

print("\nINSPECTION COMPLETE")
