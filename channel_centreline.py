
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

DATA = Path("data/raw")
OUTPUT = Path("outputs/graphs")

OUTPUT.mkdir(parents=True, exist_ok=True)

print("\nRIVERSIM — CHANNEL CENTRELINE ANALYSIS")


# ==========================================
# LOAD BANK POINTS
# ==========================================

points = gpd.read_file(
    DATA / "bank_points.gpkg"
)

# Keep only north and south bank measurements
points = points[
    points["bank"].isin(["north", "south"])
].copy()


# ==========================================
# PREPARE CHANNEL WIDTH AND CENTRE
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

# Midpoint between the two banks
table["channel_centre"] = (
    table["north_distance"]
    + table["south_distance"]
) / 2


# ==========================================
# CALCULATE CENTRELINE SHIFT
# ==========================================

baseline = table[
    table["year"] == 1990
][
    ["transect_id", "channel_centre"]
].rename(
    columns={
        "channel_centre": "centre_1990"
    }
)

table = table.merge(
    baseline,
    on="transect_id",
    how="left"
)

# Positive means movement toward the south
table["centre_shift"] = (
    table["channel_centre"]
    - table["centre_1990"]
)


# ==========================================
# SUMMARY BY YEAR
# ==========================================

summary = (
    table.groupby("year")
    .agg(
        mean_width=("channel_width", "mean"),
        median_width=("channel_width", "median"),
        mean_centre=("channel_centre", "mean"),
        mean_centre_shift=("centre_shift", "mean"),
        median_centre_shift=("centre_shift", "median")
    )
    .reset_index()
)

print("\n===== CHANNEL CENTRELINE SUMMARY =====")
print(summary.round(2).to_string(index=False))


# ==========================================
# CENTRELINE SHIFT PLOT
# ==========================================

plt.figure(figsize=(11, 6))

plt.plot(
    summary["year"],
    summary["mean_centre_shift"],
    marker="o",
    linewidth=2
)

plt.axhline(
    0,
    linestyle="--",
    linewidth=1
)

plt.title(
    "Mean Channel Centre Shift Relative to 1990"
)

plt.xlabel("Year")
plt.ylabel("Mean centre shift (m)")

plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT / "channel_centreline_shift.png",
    dpi=300
)

plt.close()


# ==========================================
# CENTRELINE SHIFT BY TRANSECT
# ==========================================

pivot = table.pivot(
    index="transect_id",
    columns="year",
    values="centre_shift"
)

plt.figure(figsize=(13, 7))

for transect_id, row in pivot.iterrows():

    plt.plot(
        pivot.columns,
        row.values,
        marker="o",
        alpha=0.7,
        label=transect_id
    )

plt.axhline(
    0,
    linestyle="--",
    linewidth=1
)

plt.title(
    "Channel Centre Shift by Transect"
)

plt.xlabel("Year")
plt.ylabel("Centre shift (m)")

plt.grid(True, alpha=0.3)

plt.legend(
    title="Transect",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.savefig(
    OUTPUT / "centreline_shift_by_transect.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==========================================
# EXPORT RESULTS
# ==========================================

table.to_csv(
    OUTPUT / "centreline_transect_results.csv",
    index=False
)

summary.to_csv(
    OUTPUT / "centreline_summary.csv",
    index=False
)

print("\n===== OUTPUTS CREATED =====")

print(
    "channel_centreline_shift.png"
)

print(
    "centreline_shift_by_transect.png"
)

print(
    "centreline_transect_results.csv"
)

print(
    "centreline_summary.csv"
)

print("\nAnalysis completed successfully.")
