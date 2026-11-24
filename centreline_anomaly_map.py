
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.lines import Line2D

# ==========================================
# CONFIGURATION
# ==========================================

DATA = Path("data/raw")
OUTPUT = Path("outputs/maps")

OUTPUT.mkdir(parents=True, exist_ok=True)

print("\nRIVERSIM — ANOMALY SPATIAL INVESTIGATION")


# ==========================================
# LOAD DATA
# ==========================================

points = gpd.read_file(DATA / "bank_points.gpkg")
transects = gpd.read_file(DATA / "transects.gpkg")
banklines = gpd.read_file(DATA / "banklines.gpkg")
water = gpd.read_file(DATA / "water_polygons.gpkg")

# All layers must use the same projected CRS.
layers = [points, transects, banklines, water]

if not all(layer.crs == points.crs for layer in layers):
    raise ValueError("Input layers have inconsistent CRS.")

print("CRS:", points.crs)


# ==========================================
# DEFINE ANOMALIES
# ==========================================

cases = [
    {
        "year": 2015,
        "transects": ["T02", "T03"],
        "title": "2015 — T02 to T03"
    },
    {
        "year": 2015,
        "transects": ["T18", "T19"],
        "title": "2015 — T18 to T19"
    },
    {
        "year": 2025,
        "transects": ["T18", "T19"],
        "title": "2025 — T18 to T19"
    }
]


# ==========================================
# CREATE DIAGNOSTIC FIGURE
# ==========================================

fig, axes = plt.subplots(
    1,
    3,
    figsize=(21, 9)
)

for ax, case in zip(axes, cases):

    year = case["year"]
    selected_ids = case["transects"]

    # Select relevant transects.
    selected_transects = transects[
        transects["transect_id"].isin(selected_ids)
    ]

    # Select bank points for this year and pair.
    selected_points = points[
        (points["year"] == year) &
        (points["transect_id"].isin(selected_ids))
    ]

    # Select banklines for this year.
    selected_banklines = banklines[
        banklines["year"] == year
    ]

    # Select water polygons for this year.
    selected_water = water[
        water["year"] == year
    ]

    # Plot water polygons.
    if not selected_water.empty:
        selected_water.plot(
            ax=ax,
            color="lightblue",
            edgecolor="steelblue",
            alpha=0.45,
            label="Water polygon"
        )

    # Plot original banklines.
    for bank, color in [
        ("north", "red"),
        ("south", "green")
    ]:

        subset = selected_banklines[
            selected_banklines["bank"] == bank
        ]

        if not subset.empty:
            subset.plot(
                ax=ax,
                color=color,
                linewidth=2,
                label=f"{bank.title()} bankline"
            )

    # Plot transects.
    selected_transects.plot(
        ax=ax,
        color="black",
        linewidth=1,
        linestyle="--",
        alpha=0.65
    )

    # Plot bank points.
    for bank, color in [
        ("north", "darkred"),
        ("south", "darkgreen")
    ]:

        subset = selected_points[
            selected_points["bank"] == bank
        ]

        if not subset.empty:

            subset.plot(
                ax=ax,
                color=color,
                markersize=55,
                edgecolor="white",
                linewidth=0.8
            )

            # Label points by transect.
            for _, row in subset.iterrows():

                ax.annotate(
                    row["transect_id"],
                    (row.geometry.x, row.geometry.y),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=8
                )

    # Set map extent around selected transects.
    bounds = selected_transects.total_bounds

    buffer = 450

    ax.set_xlim(
        bounds[0] - buffer,
        bounds[2] + buffer
    )

    ax.set_ylim(
        bounds[1] - buffer,
        bounds[3] + buffer
    )

    ax.set_aspect("equal")

    ax.set_title(
        case["title"],
        fontsize=13,
        fontweight="bold"
    )

    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")

    ax.grid(
        True,
        alpha=0.2
    )


# ==========================================
# LEGEND
# ==========================================

legend_items = [
    Line2D(
        [0], [0],
        color="red",
        linewidth=2,
        label="North bankline"
    ),
    Line2D(
        [0], [0],
        color="green",
        linewidth=2,
        label="South bankline"
    ),
    Line2D(
        [0], [0],
        marker="o",
        color="darkred",
        linestyle="None",
        label="North bank point"
    ),
    Line2D(
        [0], [0],
        marker="o",
        color="darkgreen",
        linestyle="None",
        label="South bank point"
    ),
    Line2D(
        [0], [0],
        color="black",
        linestyle="--",
        label="Transect"
    )
]

fig.legend(
    handles=legend_items,
    loc="lower center",
    ncol=5,
    bbox_to_anchor=(0.5, -0.01)
)

fig.suptitle(
    "RiverSim — Suspicious Centreline Locations",
    fontsize=17,
    fontweight="bold"
)

plt.tight_layout(
    rect=[0, 0.07, 1, 0.94]
)

plt.savefig(
    OUTPUT / "centreline_anomaly_investigation.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    "\nMap created: outputs/maps/"
    "centreline_anomaly_investigation.png"
)

print("\nInvestigation completed successfully.")
