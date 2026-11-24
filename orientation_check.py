
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data/raw")
GRAPH_DIR = Path("outputs/graphs")

GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Load datasets
water = gpd.read_file(DATA_DIR / "water_polygons.gpkg")
banklines = gpd.read_file(DATA_DIR / "banklines.gpkg")
transects = gpd.read_file(DATA_DIR / "transects.gpkg")

# Select 2025 data
water_2025 = water[water["year"] == 2025]
banks_2025 = banklines[banklines["year"] == 2025]

north = banks_2025[banks_2025["bank"] == "north"]
south = banks_2025[banks_2025["bank"] == "south"]

# Plot
fig, ax = plt.subplots(figsize=(12, 10))

water_2025.plot(
    ax=ax,
    color="lightblue",
    edgecolor="blue",
    alpha=0.6,
    label="Water polygon"
)

north.plot(
    ax=ax,
    color="red",
    linewidth=2,
    label="North bank"
)

south.plot(
    ax=ax,
    color="green",
    linewidth=2,
    label="South bank"
)

transects.plot(
    ax=ax,
    color="black",
    linewidth=0.5,
    alpha=0.5,
    label="Transects"
)

ax.set_title("Padma River - Bank Orientation Check (2025)")
ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")
ax.legend()

ax.set_aspect("equal")

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "orientation_check_2025.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Orientation map generated!")
