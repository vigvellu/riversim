
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
    index=["transect_id", "bank"],
    columns="year",
    values="distance_m"
)

years = sorted(pivot.columns)

# Calculate annualized rates between consecutive observations
records = []

for (transect, bank), row in pivot.iterrows():

    for i in range(1, len(years)):

        previous_year = years[i - 1]
        current_year = years[i]

        previous_position = row[previous_year]
        current_position = row[current_year]

        elapsed_years = current_year - previous_year

        rate = (
            current_position - previous_position
        ) / elapsed_years

        records.append({
            "transect_id": transect,
            "bank": bank,
            "start_year": previous_year,
            "end_year": current_year,
            "elapsed_years": elapsed_years,
            "migration_rate_m_per_year": rate
        })

rates = pd.DataFrame(records)

# Save detailed rates
rates.to_csv(
    REPORT_DIR / "migration_rates.csv",
    index=False
)

# Summary statistics
summary = rates.groupby(
    ["start_year", "end_year", "bank"]
)["migration_rate_m_per_year"].agg(
    ["mean", "median", "min", "max"]
).reset_index()

print("\n===== MIGRATION RATE SUMMARY =====")
print(summary.round(2).to_string(index=False))

print("\n===== LARGEST POSITIVE MOVEMENT RATES =====")
print(
    rates.nlargest(10, "migration_rate_m_per_year")
    .round(2).to_string(index=False)
)

print("\n===== LARGEST NEGATIVE MOVEMENT RATES =====")
print(
    rates.nsmallest(10, "migration_rate_m_per_year")
    .round(2).to_string(index=False)
)

# Plot average rates
fig, ax = plt.subplots(figsize=(11, 6))

intervals = sorted(
    rates[["start_year", "end_year"]]
    .drop_duplicates()
    .itertuples(index=False, name=None)
)

labels = [
    f"{start}-{end}"
    for start, end in intervals
]

for bank in ["north", "south"]:

    bank_data = (
        summary[summary["bank"] == bank]
        .sort_values("start_year")
    )

    ax.plot(
        labels,
        bank_data["mean"],
        marker="o",
        linewidth=2,
        label=f"{bank.title()} bank"
    )

ax.axhline(0, color="black", linewidth=0.8)
ax.set_title("Padma River - Average Signed Bank Migration Rate")
ax.set_xlabel("Observation interval")
ax.set_ylabel("Migration rate (m/year)")
ax.grid(alpha=0.3)
ax.legend()

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "migration_rates.png",
    dpi=300
)

plt.show()

print("\nAnalysis complete!")
print("Saved: outputs/reports/migration_rates.csv")
print("Saved: outputs/graphs/migration_rates.png")
