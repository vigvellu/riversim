
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from shapely.geometry import Point

# ==========================================
# CONFIGURATION
# ==========================================

INPUT = Path("data/processed/historical_centrelines.gpkg")
OUTPUT = Path("outputs")

GRAPHS = OUTPUT / "graphs"
REPORTS = OUTPUT / "reports"

GRAPHS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

print("\nRIVERSIM — CENTRELINE QUALITY ANALYSIS")


# ==========================================
# LOAD CENTRELINES
# ==========================================

centrelines = gpd.read_file(INPUT)

if centrelines.crs is None:
    raise ValueError("Centreline CRS is missing.")

if centrelines.crs.is_geographic:
    raise ValueError(
        "Use a projected CRS measured in metres."
    )


# ==========================================
# GEOMETRY QUALITY ANALYSIS
# ==========================================

records = []

for _, row in centrelines.iterrows():

    line = row.geometry

    if line is None or line.is_empty:
        continue

    start = Point(line.coords[0])
    end = Point(line.coords[-1])

    straight_distance = start.distance(end)

    sinuosity = (
        line.length / straight_distance
        if straight_distance > 0
        else float("nan")
    )

    segment_lengths = []

    coordinates = list(line.coords)

    for i in range(len(coordinates) - 1):

        p1 = Point(coordinates[i])
        p2 = Point(coordinates[i + 1])

        segment_lengths.append(
            p1.distance(p2)
        )

    records.append({

        "year": int(row["year"]),

        "centreline_length_m": line.length,

        "straight_distance_m": straight_distance,

        "sinuosity": sinuosity,

        "segment_count": len(segment_lengths),

        "mean_segment_length_m": (
            sum(segment_lengths) / len(segment_lengths)
        ),

        "max_segment_length_m": max(segment_lengths),

        "min_segment_length_m": min(segment_lengths),

        "is_simple": line.is_simple,

        "is_valid": line.is_valid

    })


quality = pd.DataFrame(records)


# ==========================================
# PRINT RESULTS
# ==========================================

print("\n===== CENTRELINE QUALITY SUMMARY =====")

print(
    quality.round(3).to_string(index=False)
)


# ==========================================
# CHECK FOR GEOMETRY ISSUES
# ==========================================

print("\n===== GEOMETRY CHECKS =====")

for _, row in quality.iterrows():

    issues = []

    if not row["is_valid"]:
        issues.append("Invalid geometry")

    if not row["is_simple"]:
        issues.append("Self-intersection")

    if row["sinuosity"] < 1:
        issues.append("Sinuosity below 1")

    if issues:

        print(
            f"{row['year']}: "
            + ", ".join(issues)
        )

    else:

        print(
            f"{row['year']}: No basic geometry issues detected"
        )


# ==========================================
# SINUOSITY CHART
# ==========================================

plt.figure(figsize=(10, 6))

plt.plot(
    quality["year"],
    quality["sinuosity"],
    marker="o",
    linewidth=2
)

plt.axhline(
    1,
    linestyle="--",
    label="Straight-line reference"
)

plt.title("Historical Channel Centreline Sinuosity")

plt.xlabel("Year")
plt.ylabel("Sinuosity ratio")

plt.grid(True, alpha=0.3)

plt.legend()

plt.tight_layout()

plt.savefig(
    GRAPHS / "centreline_sinuosity.png",
    dpi=300
)

plt.close()


# ==========================================
# CENTRELINE LENGTH COMPARISON
# ==========================================

plt.figure(figsize=(10, 6))

plt.plot(
    quality["year"],
    quality["centreline_length_m"] / 1000,
    marker="o",
    linewidth=2
)

plt.title("Historical Centreline Length")

plt.xlabel("Year")
plt.ylabel("Length (km)")

plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    GRAPHS / "centreline_length_comparison.png",
    dpi=300
)

plt.close()


# ==========================================
# EXPORT RESULTS
# ==========================================

quality.to_csv(
    REPORTS / "centreline_quality.csv",
    index=False
)

print("\n===== OUTPUTS CREATED =====")

print("outputs/graphs/centreline_sinuosity.png")
print("outputs/graphs/centreline_length_comparison.png")
print("outputs/reports/centreline_quality.csv")

print("\nAnalysis completed successfully.")
