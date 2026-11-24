
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

INPUT = Path("data/processed/historical_centrelines.gpkg")

OUTPUT = Path("outputs/reports")
GRAPHS = Path("outputs/graphs")

OUTPUT.mkdir(parents=True, exist_ok=True)
GRAPHS.mkdir(parents=True, exist_ok=True)

SAMPLE_COUNT = 500

print("\nRIVERSIM — HISTORICAL CENTRELINE DISPLACEMENT")

# ==========================================
# LOAD DATA
# ==========================================

gdf = gpd.read_file(INPUT)

if "year" not in gdf.columns:
    raise ValueError("The GeoPackage must contain a 'year' field.")

if gdf.crs is None or gdf.crs.is_geographic:
    raise ValueError("A projected CRS is required for metre-based distances.")

gdf["year"] = gdf["year"].astype(int)

baseline_rows = gdf[gdf["year"] == 1990]

if len(baseline_rows) != 1:
    raise ValueError("Expected exactly one 1990 baseline centreline.")

baseline = baseline_rows.geometry.iloc[0]

if baseline is None or baseline.is_empty:
    raise ValueError("The 1990 centreline is empty.")

# ==========================================
# DISPLACEMENT ANALYSIS
# ==========================================

results = []

for _, row in gdf.iterrows():

    year = int(row["year"])
    line = row.geometry

    if line is None or line.is_empty:
        continue

    distances = []

    for i in range(SAMPLE_COUNT):
        point = line.interpolate(
            line.length * i / (SAMPLE_COUNT - 1)
        )

        distances.append(point.distance(baseline))

    results.append({
        "year": year,
        "centreline_length_m": line.length,
        "length_change_m": line.length - baseline.length,
        "length_change_percent": (
            (line.length - baseline.length) / baseline.length * 100
        ),
        "mean_displacement_m": np.mean(distances),
        "median_displacement_m": np.median(distances),
        "max_displacement_m": np.max(distances),
        "min_displacement_m": np.min(distances)
    })

results = pd.DataFrame(results).sort_values("year")

# ==========================================
# SAVE RESULTS
# ==========================================

results.to_csv(
    OUTPUT / "centreline_displacement_results.csv",
    index=False
)

print("\n===== CENTRELINE DISPLACEMENT SUMMARY =====")
print(results.round(2).to_string(index=False))

# ==========================================
# DISPLACEMENT GRAPH
# ==========================================

plt.figure(figsize=(10, 6))

plt.plot(
    results["year"],
    results["mean_displacement_m"],
    marker="o",
    label="Mean displacement"
)

plt.plot(
    results["year"],
    results["max_displacement_m"],
    marker="s",
    label="Maximum displacement"
)

plt.xlabel("Year")
plt.ylabel("Distance from 1990 centreline (m)")
plt.title("Historical Centreline Displacement")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    GRAPHS / "centreline_displacement.png",
    dpi=300
)

plt.close()

# ==========================================
# LENGTH CHANGE GRAPH
# ==========================================

plt.figure(figsize=(10, 6))

plt.bar(
    results["year"].astype(str),
    results["length_change_m"]
)

plt.axhline(0, linewidth=1)

plt.xlabel("Year")
plt.ylabel("Length difference from 1990 (m)")
plt.title("Historical Centreline Length Change")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    GRAPHS / "centreline_length_change.png",
    dpi=300
)

plt.close()

print("\nFiles created:")
print("- outputs/reports/centreline_displacement_results.csv")
print("- outputs/graphs/centreline_displacement.png")
print("- outputs/graphs/centreline_length_change.png")

print("\nCentreline displacement analysis completed successfully.")
