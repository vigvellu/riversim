
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data/raw")
REPORT_DIR = Path("outputs/reports")
GRAPH_DIR = Path("outputs/graphs")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Load bank measurements
points = gpd.read_file(
    DATA_DIR / "bank_points.gpkg"
)

# Organize by transect, bank and year
pivot = points.pivot(
    index="transect_id",
    columns=["bank", "year"],
    values="distance_m"
)

years = sorted(points["year"].unique())

records = []

for transect, row in pivot.iterrows():

    for i in range(1, len(years)):

        start = years[i - 1]
        end = years[i]

        north_start = row[("north", start)]
        south_start = row[("south", start)]

        north_end = row[("north", end)]
        south_end = row[("south", end)]

        # Channel widths
        width_start = south_start - north_start
        width_end = south_end - north_end

        width_change = width_end - width_start

        elapsed = end - start

        width_rate = width_change / elapsed

        # Channel centre positions
        centre_start = (north_start + south_start) / 2
        centre_end = (north_end + south_end) / 2

        centre_shift = centre_end - centre_start
        centre_rate = centre_shift / elapsed

        if width_change > 0:
            condition = "Widening"
        elif width_change < 0:
            condition = "Narrowing"
        else:
            condition = "Stable"

        records.append({
            "transect_id": transect,
            "start_year": start,
            "end_year": end,
            "width_start_m": width_start,
            "width_end_m": width_end,
            "width_change_m": width_change,
            "width_change_rate_m_per_year": width_rate,
            "centre_shift_m": centre_shift,
            "centre_shift_rate_m_per_year": centre_rate,
            "condition": condition
        })

results = pd.DataFrame(records)

# Save detailed results
results.to_csv(
    REPORT_DIR / "channel_change_results.csv",
    index=False
)

# Summary by observation period
summary = results.groupby(
    ["start_year", "end_year"]
).agg(
    mean_width_change=("width_change_m", "mean"),
    median_width_change=("width_change_m", "median"),
    mean_width_rate=("width_change_rate_m_per_year", "mean"),
    mean_centre_shift=("centre_shift_m", "mean"),
    mean_centre_rate=("centre_shift_rate_m_per_year", "mean")
).round(2)

print("\n===== CHANNEL CHANGE SUMMARY =====")
print(summary.to_string())

print("\n===== WIDENING / NARROWING COUNTS =====")

counts = results.groupby(
    ["start_year", "end_year", "condition"]
).size().unstack(fill_value=0)

print(counts.to_string())

# Plot width change rate
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

labels = [
    f"{start}-{end}"
    for start, end in zip(
        summary.index.get_level_values("start_year"),
        summary.index.get_level_values("end_year")
    )
]

axes[0].bar(
    labels,
    summary["mean_width_rate"]
)

axes[0].axhline(0, color="black", linewidth=0.8)
axes[0].set_title("Average Channel Widening / Narrowing")
axes[0].set_ylabel("Width change (m/year)")
axes[0].grid(axis="y", alpha=0.3)

axes[1].bar(
    labels,
    summary["mean_centre_rate"]
)

axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].set_title("Average Channel Centre Shift")
axes[1].set_ylabel("Centre shift (m/year)")
axes[1].grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "channel_change.png",
    dpi=300
)

plt.show()

print("\nChannel change analysis complete!")
