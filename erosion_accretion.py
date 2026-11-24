
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data/raw")
REPORT_DIR = Path("outputs/reports")
GRAPH_DIR = Path("outputs/graphs")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

points = gpd.read_file(
    DATA_DIR / "bank_points.gpkg"
)

pivot = points.pivot(
    index=["transect_id", "bank"],
    columns="year",
    values="distance_m"
)

years = sorted(pivot.columns)

records = []

for (transect, bank), row in pivot.iterrows():

    for i in range(1, len(years)):

        start_year = years[i - 1]
        end_year = years[i]

        displacement = (
            row[end_year] - row[start_year]
        )

        elapsed = end_year - start_year

        # Corrected landward retreat convention
        if bank == "north":
            retreat = -displacement
        else:
            retreat = displacement

        rate = retreat / elapsed

        if rate > 0:
            classification = "Retreat"
        elif rate < 0:
            classification = "Advance"
        else:
            classification = "Stable"

        records.append({
            "transect_id": transect,
            "bank": bank,
            "start_year": start_year,
            "end_year": end_year,
            "displacement_m": displacement,
            "retreat_m": retreat,
            "retreat_rate_m_per_year": rate,
            "classification": classification
        })

results = pd.DataFrame(records)

# Save detailed interval results
results.to_csv(
    REPORT_DIR / "interval_retreat_advance.csv",
    index=False
)

# Summary by period and bank
summary = results.groupby(
    ["start_year", "end_year", "bank", "classification"]
).size().unstack(fill_value=0)

print("\n===== RETREAT / ADVANCE COUNTS BY PERIOD =====")
print(summary.to_string())

print("\n===== AVERAGE RETREAT RATE BY PERIOD =====")

average_rates = results.groupby(
    ["start_year", "end_year", "bank"]
)["retreat_rate_m_per_year"].agg(
    ["mean", "median", "min", "max"]
).round(2)

print(average_rates.to_string())

# Plot mean landward retreat rate
fig, ax = plt.subplots(figsize=(12, 6))

for bank in ["north", "south"]:

    data = (
        average_rates
        .loc[(slice(None), slice(None), bank), :]
        .reset_index()
    )

    labels = (
        data["start_year"].astype(str)
        + "-"
        + data["end_year"].astype(str)
    )

    ax.plot(
        labels,
        data["mean"],
        marker="o",
        linewidth=2,
        label=bank.title() + " bank"
    )

ax.axhline(0, color="black", linewidth=0.8)
ax.set_title("Mean Landward Retreat Rate by Observation Period")
ax.set_xlabel("Period")
ax.set_ylabel("Signed retreat rate (m/year)")
ax.grid(alpha=0.3)
ax.legend()

plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "corrected_retreat_rates.png",
    dpi=300
)

plt.show()

print("\nCorrected interval analysis complete!")

