
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from pathlib import Path
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

# ==========================================
# CONFIGURATION
# ==========================================

DATA = Path("data")

BANK_FILE = DATA / "raw" / "banklines.gpkg"
WATER_FILE = DATA / "raw" / "water_polygons.gpkg"
TRANSECT_FILE = DATA / "raw" / "transects.gpkg"
CENTRELINE_FILE = DATA / "processed" / "historical_centrelines.gpkg"

OUTPUT = Path("outputs/maps")
OUTPUT.mkdir(parents=True, exist_ok=True)

YEARS = [1990, 2000, 2010, 2015, 2020, 2025]

print("\nRIVERSIM — HISTORICAL SPATIAL CHANGE VISUALIZATION")

# ==========================================
# LOAD GIS DATA
# ==========================================

banklines = gpd.read_file(BANK_FILE)
water = gpd.read_file(WATER_FILE)
transects = gpd.read_file(TRANSECT_FILE)
centrelines = gpd.read_file(CENTRELINE_FILE)

layers = {
    "Banklines": banklines,
    "Water polygons": water,
    "Transects": transects,
    "Centrelines": centrelines
}

for name, layer in layers.items():

    if layer.crs is None:
        raise ValueError(f"{name} has no CRS.")

    if layer.crs != banklines.crs:
        raise ValueError(
            f"{name} CRS does not match the bankline CRS."
        )

    if layer.empty:
        raise ValueError(f"{name} layer is empty.")

# ==========================================
# VALIDATE REQUIRED FIELDS
# ==========================================

required_fields = {
    "banklines": {"year", "bank"},
    "water": {"year"},
    "transects": {"transect_id"},
    "centrelines": {"year"}
}

for name, required in required_fields.items():

    layer = {
        "banklines": banklines,
        "water": water,
        "transects": transects,
        "centrelines": centrelines
    }[name]

    missing = required - set(layer.columns)

    if missing:
        raise ValueError(
            f"{name} is missing fields: {missing}"
        )

for layer in [banklines, water, centrelines]:
    layer["year"] = pd.to_numeric(
        layer["year"],
        errors="raise"
    ).astype(int)

# ==========================================
# CHECK AVAILABLE YEARS
# ==========================================

for name, layer in [
    ("Banklines", banklines),
    ("Water polygons", water),
    ("Centrelines", centrelines)
]:

    available = sorted(layer["year"].unique())

    print(f"{name} years: {available}")

    missing = set(YEARS) - set(available)

    if missing:
        raise ValueError(
            f"{name} is missing years: {sorted(missing)}"
        )

# ==========================================
# COMMON MAP EXTENT
# ==========================================

combined = gpd.GeoDataFrame(
    geometry=pd.concat([
        banklines.geometry,
        water.geometry,
        transects.geometry,
        centrelines.geometry
    ], ignore_index=True),
    crs=banklines.crs
)

minx, miny, maxx, maxy = combined.total_bounds

x_padding = (maxx - minx) * 0.05
y_padding = (maxy - miny) * 0.05

x_limits = (
    minx - x_padding,
    maxx + x_padding
)

y_limits = (
    miny - y_padding,
    maxy + y_padding
)

# ==========================================
# MAP 1 — SIX HISTORICAL PANELS
# ==========================================

fig, axes = plt.subplots(
    2,
    3,
    figsize=(19, 12)
)

axes = axes.flatten()

for ax, year in zip(axes, YEARS):

    yearly_water = water[water["year"] == year]

    yearly_banks = banklines[
        banklines["year"] == year
    ]

    yearly_centreline = centrelines[
        centrelines["year"] == year
    ]

    # Background transects
    transects.plot(
        ax=ax,
        color="grey",
        linewidth=0.5,
        alpha=0.25,
        zorder=1
    )

    # Water polygon
    yearly_water.plot(
        ax=ax,
        color="lightskyblue",
        edgecolor="steelblue",
        linewidth=0.8,
        alpha=0.45,
        zorder=2
    )

    # North bank
    north = yearly_banks[
        yearly_banks["bank"].str.lower() == "north"
    ]

    north.plot(
        ax=ax,
        color="royalblue",
        linewidth=1.8,
        zorder=3
    )

    # South bank
    south = yearly_banks[
        yearly_banks["bank"].str.lower() == "south"
    ]

    south.plot(
        ax=ax,
        color="darkorange",
        linewidth=1.8,
        zorder=3
    )

    # Reconstructed centreline
    yearly_centreline.plot(
        ax=ax,
        color="darkred",
        linewidth=2,
        linestyle="--",
        zorder=4
    )

    ax.set_xlim(x_limits)
    ax.set_ylim(y_limits)

    ax.set_title(
        f"River morphology — {year}",
        fontsize=12,
        fontweight="bold"
    )

    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.grid(alpha=0.15)

# Shared legend
legend_items = [
    Patch(
        facecolor="lightskyblue",
        edgecolor="steelblue",
        alpha=0.45,
        label="Water polygon"
    ),
    Line2D(
        [0], [0],
        color="royalblue",
        linewidth=2,
        label="North bank"
    ),
    Line2D(
        [0], [0],
        color="darkorange",
        linewidth=2,
        label="South bank"
    ),
    Line2D(
        [0], [0],
        color="darkred",
        linestyle="--",
        linewidth=2,
        label="Reconstructed centreline"
    ),
    Line2D(
        [0], [0],
        color="grey",
        alpha=0.5,
        linewidth=1,
        label="Transects"
    )
]

fig.legend(
    handles=legend_items,
    loc="lower center",
    ncol=5,
    fontsize=10
)

fig.suptitle(
    "Padma River — Historical Spatial Change (1990–2025)",
    fontsize=17,
    fontweight="bold"
)

plt.tight_layout(rect=[0, 0.07, 1, 0.94])

plt.savefig(
    OUTPUT / "historical_spatial_change.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# MAP 2 — COMBINED HISTORICAL OVERLAY
# ==========================================

fig, ax = plt.subplots(figsize=(14, 11))

colors = plt.cm.viridis(
    np.linspace(0.05, 0.95, len(YEARS))
)

for year, color in zip(YEARS, colors):

    yearly_water = water[
        water["year"] == year
    ]

    yearly_banks = banklines[
        banklines["year"] == year
    ]

    yearly_centreline = centrelines[
        centrelines["year"] == year
    ]

    # Water polygon outlines and light fills
    yearly_water.plot(
        ax=ax,
        facecolor=color,
        edgecolor=color,
        linewidth=1,
        alpha=0.10,
        zorder=1
    )

    # Banklines
    for bank, linestyle in [
        ("north", "-"),
        ("south", "--")
    ]:

        subset = yearly_banks[
            yearly_banks["bank"].str.lower() == bank
        ]

        subset.plot(
            ax=ax,
            color=color,
            linewidth=1.6,
            linestyle=linestyle,
            zorder=2
        )

    # Reconstructed centreline
    yearly_centreline.plot(
        ax=ax,
        color=color,
        linewidth=2.2,
        linestyle=":",
        zorder=3
    )

# Transects in background
transects.plot(
    ax=ax,
    color="grey",
    linewidth=0.5,
    alpha=0.25,
    zorder=0
)

ax.set_xlim(x_limits)
ax.set_ylim(y_limits)

ax.set_aspect("equal")

ax.set_title(
    "Padma River — Combined Historical Spatial Overlay",
    fontsize=16,
    fontweight="bold"
)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")
ax.grid(alpha=0.2)

# Year legend
year_handles = [
    Line2D(
        [0], [0],
        color=color,
        linewidth=3,
        label=str(year)
    )
    for year, color in zip(YEARS, colors)
]

ax.legend(
    handles=year_handles,
    title="Survey year",
    loc="best"
)

plt.tight_layout()

plt.savefig(
    OUTPUT / "historical_all_years_overlay.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# FINAL OUTPUT
# ==========================================

print("\n===== VISUALIZATION SUMMARY =====")

for year in YEARS:

    print(
        f"{year}: "
        f"{len(water[water.year == year])} water polygons, "
        f"{len(banklines[banklines.year == year])} banklines, "
        f"{len(centrelines[centrelines.year == year])} centrelines"
    )

print("\nFiles created:")

print("- outputs/maps/historical_spatial_change.png")
print("- outputs/maps/historical_all_years_overlay.png")

print("\nHistorical spatial visualization completed successfully.")
