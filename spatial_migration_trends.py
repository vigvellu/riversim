
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# ==========================================
# CONFIGURATION
# ==========================================

BANK_FILE = Path("data/raw/bank_points.gpkg")
TRANSECT_FILE = Path("data/raw/transects.gpkg")

REPORT_DIR = Path("outputs/reports")
GRAPH_DIR = Path("outputs/graphs")
MAP_DIR = Path("outputs/maps")

for folder in [REPORT_DIR, GRAPH_DIR, MAP_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

STABILITY_THRESHOLD = 15

print("\nRIVERSIM — SPATIAL MIGRATION TREND ANALYSIS")

# ==========================================
# LOAD DATA
# ==========================================

banks = gpd.read_file(BANK_FILE)
transects = gpd.read_file(TRANSECT_FILE)

if banks.crs is None or transects.crs is None:
    raise ValueError("Missing CRS information.")

if banks.crs != transects.crs:
    raise ValueError("Bank points and transects must use the same CRS.")

required = {"year", "bank", "transect_id", "distance_m"}

if not required.issubset(banks.columns):
    raise ValueError(
        f"Missing bank point fields: {required - set(banks.columns)}"
    )

if "transect_id" not in transects.columns:
    raise ValueError("Transects must contain transect_id.")

banks["year"] = banks["year"].astype(int)

# ==========================================
# CALCULATE CHANNEL CENTRE POSITIONS
# ==========================================

pivot = banks.pivot_table(
    index=["year", "transect_id"],
    columns="bank",
    values="distance_m",
    aggfunc="mean"
).reset_index()

if not {"north", "south"}.issubset(pivot.columns):
    raise ValueError("Both north and south bank measurements are required.")

if pivot[["north", "south"]].isna().any().any():
    raise ValueError("Some transects are missing bank measurements.")

pivot["centre_distance_m"] = (
    pivot["north"] + pivot["south"]
) / 2

years = sorted(pivot["year"].unique())

if len(years) < 2:
    raise ValueError("At least two survey years are required.")

# ==========================================
# CALCULATE MOVEMENT BY TRANSECT
# ==========================================

interval_results = []

for i in range(len(years) - 1):

    start_year = years[i]
    end_year = years[i + 1]

    start = pivot[pivot["year"] == start_year][
        ["transect_id", "centre_distance_m"]
    ].rename(columns={
        "centre_distance_m": "start_centre_m"
    })

    end = pivot[pivot["year"] == end_year][
        ["transect_id", "centre_distance_m"]
    ].rename(columns={
        "centre_distance_m": "end_centre_m"
    })

    merged = start.merge(
        end,
        on="transect_id",
        how="inner",
        validate="one_to_one"
    )

    if merged.empty:
        raise ValueError(
            f"No matching transects for {start_year}–{end_year}."
        )

    merged["start_year"] = start_year
    merged["end_year"] = end_year

    # Positive = southward
    # Negative = northward

    merged["displacement_m"] = (
        merged["end_centre_m"] - merged["start_centre_m"]
    )

    duration = end_year - start_year

    merged["annual_rate_m"] = (
        merged["displacement_m"] / duration
    )

    merged["direction"] = np.select(
        [
            merged["displacement_m"] > STABILITY_THRESHOLD,
            merged["displacement_m"] < -STABILITY_THRESHOLD
        ],
        [
            "Southward",
            "Northward"
        ],
        default="Stable"
    )

    interval_results.append(merged)

movement = pd.concat(
    interval_results,
    ignore_index=True
)

# ==========================================
# SAVE TRANSECT RESULTS
# ==========================================

movement.to_csv(
    REPORT_DIR / "spatial_migration_by_transect.csv",
    index=False
)

# ==========================================
# INTERVAL SUMMARY
# ==========================================

summary = movement.groupby(
    ["start_year", "end_year"]
).agg(
    mean_displacement_m=("displacement_m", "mean"),
    median_displacement_m=("displacement_m", "median"),
    max_displacement_m=("displacement_m", "max"),
    min_displacement_m=("displacement_m", "min"),
    mean_annual_rate=("annual_rate_m", "mean"),
    southward_count=(
        "direction",
        lambda x: (x == "Southward").sum()
    ),
    northward_count=(
        "direction",
        lambda x: (x == "Northward").sum()
    ),
    stable_count=(
        "direction",
        lambda x: (x == "Stable").sum()
    )
).reset_index()

summary.to_csv(
    REPORT_DIR / "spatial_migration_interval_summary.csv",
    index=False
)

print("\n===== MIGRATION BY HISTORICAL INTERVAL =====")
print(summary.round(2).to_string(index=False))

# ==========================================
# SPATIAL MOVEMENT MAP
# ==========================================

map_data = transects.merge(
    movement,
    on="transect_id",
    how="inner",
    validate="one_to_many"
)

if map_data.empty:
    raise ValueError("No matching transect geometries found.")

grouped = list(
    map_data.groupby(["start_year", "end_year"])
)

limit = max(
    abs(map_data["displacement_m"].min()),
    abs(map_data["displacement_m"].max()),
    STABILITY_THRESHOLD
)

norm = Normalize(vmin=-limit, vmax=limit)

fig, axes = plt.subplots(
    2, 3,
    figsize=(17, 11)
)

axes = axes.flatten()

for i, ((start_year, end_year), group) in enumerate(grouped):

    ax = axes[i]

    group.plot(
        ax=ax,
        column="displacement_m",
        cmap="coolwarm",
        norm=norm,
        linewidth=3,
        legend=False
    )

    ax.set_title(
        f"{start_year}–{end_year}",
        fontsize=12
    )

    ax.set_aspect("equal")
    ax.set_axis_off()

# Remove unused subplot
for ax in axes[len(grouped):]:
    ax.remove()

sm = ScalarMappable(norm=norm, cmap="coolwarm")
sm.set_array([])

fig.colorbar(
    sm,
    ax=axes[:len(grouped)].tolist(),
    label="Centreline displacement (m)\nNegative = Northward | Positive = Southward",
    shrink=0.75
)

fig.suptitle(
    "Spatial River Centreline Migration by Historical Interval",
    fontsize=15
)

plt.savefig(
    MAP_DIR / "spatial_migration_trends.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# MOVEMENT HEATMAP
# ==========================================

heatmap = movement.pivot(
    index="transect_id",
    columns=["start_year", "end_year"],
    values="displacement_m"
)

heatmap = heatmap.sort_index()

plt.figure(figsize=(12, 8))

plt.imshow(
    heatmap.values,
    aspect="auto",
    cmap="coolwarm",
    vmin=-limit,
    vmax=limit
)

plt.colorbar(
    label="Centreline displacement (m)"
)

plt.xticks(
    range(len(heatmap.columns)),
    [f"{a}–{b}" for a, b in heatmap.columns],
    rotation=30
)

plt.yticks(
    range(len(heatmap.index)),
    heatmap.index
)

plt.xlabel("Historical interval")
plt.ylabel("Transect")
plt.title("Transect-wise Centreline Migration Heatmap")

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "spatial_migration_trends_heatmap.png",
    dpi=300
)

plt.close()

# ==========================================
# MOVEMENT CLASSIFICATION
# ==========================================

print("\n===== MOVEMENT CLASSIFICATION =====")

classification = movement.groupby(
    ["start_year", "end_year", "direction"]
).size().unstack(fill_value=0)

print(classification.to_string())

# ==========================================
# FINAL OUTPUT
# ==========================================

print("\nFiles created:")

print("- outputs/reports/spatial_migration_by_transect.csv")
print("- outputs/reports/spatial_migration_interval_summary.csv")
print("- outputs/maps/spatial_migration_trends.png")
print("- outputs/graphs/spatial_migration_trends_heatmap.png")

print("\nSpatial migration analysis completed successfully.")
