
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("outputs")
GRAPH_DIR = OUTPUT_DIR / "graphs"

GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Load transects and migration rates
transects = gpd.read_file(DATA_DIR / "transects.gpkg")
rates = pd.read_csv(
    OUTPUT_DIR / "reports" / "migration_rates.csv"
)

# Select the 2010-2015 interval
period = rates[
    (rates["start_year"] == 2010) &
    (rates["end_year"] == 2015)
].copy()

# Calculate a representative point for each transect
transects["geometry"] = transects.geometry.interpolate(
    transects.geometry.length / 2
)

# Plot north and south banks separately
fig, axes = plt.subplots(
    1, 2,
    figsize=(15, 8)
)

for ax, bank in zip(axes, ["north", "south"]):

    bank_data = period[
        period["bank"] == bank
    ]

    merged = transects.merge(
        bank_data,
        on="transect_id"
    )

    merged.plot(
        ax=ax,
        column="migration_rate_m_per_year",
        cmap="RdYlBu",
        legend=True,
        markersize=100,
        edgecolor="black",
        legend_kwds={
            "label": "Migration rate (m/year)"
        }
    )

    ax.set_title(
        f"{bank.title()} Bank: 2010–2015"
    )

    ax.set_axis_off()

plt.suptitle(
    "Spatial Distribution of Bank Migration Rates",
    fontsize=15
)

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "spatial_migration_2010_2015.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Spatial analysis complete!")
