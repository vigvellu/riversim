
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("outputs")
GRAPH_DIR = OUTPUT_DIR / "graphs"
REPORT_DIR = OUTPUT_DIR / "reports"

GRAPH_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load bank points
points = gpd.read_file(DATA_DIR / "bank_points.gpkg")

# Organize bank positions
pivot = points.pivot(
    index=["transect_id", "year"],
    columns="bank",
    values="distance_m"
).reset_index()

# Calculate channel width and center position
pivot["channel_width_m"] = (
    pivot["south"] - pivot["north"]
)

pivot["center_position_m"] = (
    pivot["south"] + pivot["north"]
) / 2

# Sort results
pivot = pivot.sort_values(
    ["transect_id", "year"]
)

# Save detailed results
pivot.to_csv(
    REPORT_DIR / "channel_measurements.csv",
    index=False
)

# Summary by year
summary = pivot.groupby("year").agg(
    mean_width=("channel_width_m", "mean"),
    median_width=("channel_width_m", "median"),
    mean_center=("center_position_m", "mean"),
    inverted_transects=(
        "channel_width_m",
        lambda x: (x <= 0).sum()
    )
).reset_index()

print("\n===== CHANNEL MEASUREMENTS =====")
print(summary.to_string(index=False))

print("\n===== WIDTH BY TRANSECT =====")
print(
    pivot.pivot(
        index="transect_id",
        columns="year",
        values="channel_width_m"
    ).to_string()
)

print("\n===== INVALID WIDTH CHECK =====")
print(
    pivot[pivot["channel_width_m"] <= 0][
        ["transect_id", "year", "north", "south",
         "channel_width_m"]
    ].to_string(index=False)
)

# Plot average channel width
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(
    summary["year"],
    summary["mean_width"],
    marker="o",
    linewidth=2,
    label="Mean channel width"
)

ax.set_title("Padma River - Average Channel Width")
ax.set_xlabel("Year")
ax.set_ylabel("Width (m)")
ax.set_xticks(summary["year"])
ax.grid(alpha=0.3)
ax.legend()

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "channel_width.png",
    dpi=300
)

plt.show()

print("\nAnalysis complete!")
