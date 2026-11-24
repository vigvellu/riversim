
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("outputs/maps")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the historical datasets
banks = gpd.read_file(DATA_DIR / "banklines.gpkg")
water = gpd.read_file(DATA_DIR / "water_polygons.gpkg")
transects = gpd.read_file(DATA_DIR / "transects.gpkg")

# Ensure all layers use the same CRS
water = water.to_crs(banks.crs)
transects = transects.to_crs(banks.crs)

years = sorted(banks["year"].unique())

# One colour per observation year
cmap = plt.get_cmap("viridis")
year_colours = {
    year: cmap(i / max(len(years) - 1, 1))
    for i, year in enumerate(years)
}

fig, ax = plt.subplots(figsize=(14, 12))

# Draw water polygons first, underneath the banklines
for year in years:
    yearly_water = water[water["year"] == year]

    yearly_water.plot(
        ax=ax,
        color=year_colours[year],
        alpha=0.10,
        edgecolor=year_colours[year],
        linewidth=1
    )

# Draw banklines over the water polygons
for year in years:
    for bank in ["north", "south"]:
        subset = banks[
            (banks["year"] == year) &
            (banks["bank"] == bank)
        ]

        subset.plot(
            ax=ax,
            color=year_colours[year],
            linewidth=2.0,
            linestyle="-" if bank == "north" else "--"
        )

# Draw transects lightly for spatial reference
transects.plot(
    ax=ax,
    color="grey",
    linewidth=0.35,
    alpha=0.35
)

# Year legend
for year in years:
    ax.plot(
        [], [],
        color=year_colours[year],
        linewidth=2.5,
        label=str(year)
    )

ax.set_title(
    "Historical Padma River Bankline Overlay (1990–2025)",
    fontsize=15
)
ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")
ax.set_aspect("equal")
ax.grid(alpha=0.2)

ax.legend(title="Observation year")
plt.tight_layout()

output_path = OUTPUT_DIR / "historical_bankline_overlay.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.show()

print(f"\nOverlay saved to: {output_path}")
print("\nLine styles: solid = north bank | dashed = south bank")
print("Colours represent observation years.")
