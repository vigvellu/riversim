
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data/raw")
REPORT_DIR = Path("outputs/reports")
GRAPH_DIR = Path("outputs/graphs")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Load bank-point measurements
points = gpd.read_file(
    DATA_DIR / "bank_points.gpkg"
)

# Organize measurements by transect and bank
pivot = points.pivot(
    index=["transect_id", "bank"],
    columns="year",
    values="distance_m"
)

# Calculate long-term movement
results = []

for (transect, bank), row in pivot.iterrows():

    first_position = row[1990]
    last_position = row[2025]

    nsm = last_position - first_position

    epr = nsm / (2025 - 1990)

    results.append({
        "transect_id": transect,
        "bank": bank,
        "start_year": 1990,
        "end_year": 2025,
        "NSM_m": nsm,
        "EPR_m_per_year": epr,
        "absolute_movement_m": abs(nsm)
    })

results = pd.DataFrame(results)

# Save individual transect results
results.to_csv(
    REPORT_DIR / "nsm_epr_results.csv",
    index=False
)

# Summary by bank
summary = results.groupby("bank").agg(
    mean_NSM=("NSM_m", "mean"),
    median_NSM=("NSM_m", "median"),
    mean_EPR=("EPR_m_per_year", "mean"),
    median_EPR=("EPR_m_per_year", "median"),
    maximum_absolute_movement=(
        "absolute_movement_m", "max"
    )
).reset_index()

print("\n===== LONG-TERM NSM AND EPR SUMMARY =====")
print(summary.round(2).to_string(index=False))

print("\n===== RESULTS BY TRANSECT =====")
print(
    results.sort_values(
        "absolute_movement_m",
        ascending=False
    ).round(2).to_string(index=False)
)

# Plot EPR by transect
fig, ax = plt.subplots(figsize=(13, 6))

for bank in ["north", "south"]:

    bank_data = results[
        results["bank"] == bank
    ].sort_values("transect_id")

    ax.plot(
        bank_data["transect_id"],
        bank_data["EPR_m_per_year"],
        marker="o",
        label=f"{bank.title()} bank"
    )

ax.axhline(0, color="black", linewidth=0.8)
ax.set_title("Long-Term Bank Migration Rate (1990–2025)")
ax.set_xlabel("Transect")
ax.set_ylabel("EPR (m/year)")
ax.grid(alpha=0.3)
ax.legend()

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "long_term_epr.png",
    dpi=300
)

plt.show()

print("\nNSM and EPR analysis complete!")
