
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Project directories
DATA_DIR = Path("data/raw")
REPORT_DIR = Path("outputs/reports")
GRAPH_DIR = Path("outputs/graphs")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Load bank points
points = gpd.read_file(DATA_DIR / "bank_points.gpkg")

# Organize observations
pivot = points.pivot(
    index=["transect_id", "bank"],
    columns="year",
    values="distance_m"
)

# Calculate displacement relative to 1990
baseline_year = 1990

displacement = pivot.subtract(
    pivot[baseline_year],
    axis=0
)

displacement = displacement.reset_index()

# Save detailed results
output_csv = REPORT_DIR / "bank_displacement.csv"
displacement.to_csv(output_csv, index=False)

# Calculate average displacement by bank and year
summary = displacement.melt(
    id_vars=["transect_id", "bank"],
    var_name="year",
    value_name="displacement_m"
)

summary["year"] = summary["year"].astype(int)

average = summary.groupby(
    ["year", "bank"]
)["displacement_m"].mean().reset_index()

median = summary.groupby(
    ["year", "bank"]
)["displacement_m"].median().reset_index()

print("\n===== AVERAGE BANK DISPLACEMENT =====")
print(average.to_string(index=False))

print("\n===== MEDIAN BANK DISPLACEMENT =====")
print(median.to_string(index=False))

print("\n===== INDIVIDUAL TRANSECT RESULTS =====")
print(displacement.to_string(index=False))

# Plot average displacement
fig, ax = plt.subplots(figsize=(11, 6))

for bank in ["north", "south"]:
    data = average[average["bank"] == bank]

    ax.plot(
        data["year"],
        data["displacement_m"],
        marker="o",
        linewidth=2,
        label=f"{bank.title()} bank"
    )

ax.axhline(0, color="black", linewidth=0.8)
ax.set_title(
    "Padma River - Average Bank Displacement Since 1990"
)
ax.set_xlabel("Year")
ax.set_ylabel("Signed displacement (m)")
ax.set_xticks(sorted(points["year"].unique()))
ax.grid(True, alpha=0.3)
ax.legend()

plt.tight_layout()

graph_path = GRAPH_DIR / "average_bank_displacement.png"
plt.savefig(graph_path, dpi=300)
plt.show()

print(f"\nCSV saved: {output_csv}")
print(f"Graph saved: {graph_path}")
