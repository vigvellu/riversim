
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.lines import Line2D

# ==========================================
# CONFIGURATION
# ==========================================

RAW_DIR = Path("data/raw")
REPORT_DIR = Path("outputs/reports")
MAP_DIR = Path("outputs/maps")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
MAP_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1990
END_YEAR = 2025

print("\nRIVERSIM — HISTORICAL EROSION HOTSPOT MAPPING")


# ==========================================
# LOAD DATA
# ==========================================

erosion = pd.read_csv(
    REPORT_DIR / "erosion_accretion_by_transect.csv"
)

bank_points = gpd.read_file(
    RAW_DIR / "bank_points.gpkg"
)

water = gpd.read_file(
    RAW_DIR / "water_polygons.gpkg"
)

banklines = gpd.read_file(
    RAW_DIR / "banklines.gpkg"
)

print("\n===== INPUT DATA =====")

print("Erosion records:", len(erosion))
print("Bank points:", len(bank_points))
print("Water polygons:", len(water))
print("Banklines:", len(banklines))


# ==========================================
# VALIDATE DATA
# ==========================================

required = {
    "transect_id",
    "bank",
    "displacement_m",
    "retreat_m",
    "retreat_rate_m_per_year",
    "classification"
}

missing = required - set(erosion.columns)

if missing:
    raise ValueError(
        f"Missing erosion columns: {sorted(missing)}"
    )

if "year" not in bank_points.columns:
    raise ValueError("Bank points file has no year column.")

if not {"transect_id", "bank", "geometry"}.issubset(
    bank_points.columns
):
    raise ValueError(
        "Bank points file is missing required fields."
    )

if bank_points.crs is None:
    raise ValueError("Bank points have no CRS.")

if not erosion["bank"].isin(["north", "south"]).all():
    raise ValueError("Unexpected bank values.")

print("Input validation successful.")


# ==========================================
# SELECT 2025 BANK POSITIONS
# ==========================================

current_points = bank_points[
    bank_points["year"] == END_YEAR
].copy()

if current_points.empty:
    raise ValueError(
        f"No bank points found for {END_YEAR}."
    )

# Reproject background layers to bank-point CRS.
if water.crs != bank_points.crs:
    water = water.to_crs(bank_points.crs)

if banklines.crs != bank_points.crs:
    banklines = banklines.to_crs(bank_points.crs)


# ==========================================
# MERGE EROSION RESULTS WITH LOCATIONS
# ==========================================

mapped = erosion.merge(
    current_points[
        ["transect_id", "bank", "geometry"]
    ],
    on=["transect_id", "bank"],
    how="left",
    validate="one_to_one"
)

if mapped["geometry"].isna().any():
    missing_locations = mapped[
        mapped["geometry"].isna()
    ][["transect_id", "bank"]]

    raise ValueError(
        "Some erosion records have no matching 2025 bank point:\n"
        + missing_locations.to_string(index=False)
    )

mapped = gpd.GeoDataFrame(
    mapped,
    geometry="geometry",
    crs=bank_points.crs
)

mapped["longitude_projected"] = mapped.geometry.x
mapped["latitude_projected"] = mapped.geometry.y

mapped["study_period"] = (
    f"{START_YEAR}-{END_YEAR}"
)

print("\nMapped records:", len(mapped))


# ==========================================
# SAVE SPATIAL HOTSPOT DATA
# ==========================================

mapped.to_csv(
    REPORT_DIR / "erosion_hotspot_spatial_data.csv",
    index=False
)


# ==========================================
# SELECT 2025 BACKGROUND FEATURES
# ==========================================

water_2025 = water[
    water["year"] == END_YEAR
]

banklines_2025 = banklines[
    banklines["year"] == END_YEAR
]


# ==========================================
# MAP CLASSIFICATION SETTINGS
# ==========================================

class_colors = {
    "Retreat": "#d73027",
    "Advance": "#2166ac",
    "Stable": "#999999"
}

bank_names = {
    "north": "North Bank",
    "south": "South Bank"
}


# ==========================================
# CREATE TWO-PANEL HOTSPOT MAP
# ==========================================

fig, axes = plt.subplots(
    1,
    2,
    figsize=(17, 10)
)

for ax, bank in zip(
    axes,
    ["north", "south"]
):

    subset = mapped[
        mapped["bank"] == bank
    ].copy()

    # Background water area
    if not water_2025.empty:

        water_2025.plot(
            ax=ax,
            color="#b9dce9",
            edgecolor="#477f99",
            alpha=0.65,
            linewidth=0.8
        )

    # Current banklines
    if not banklines_2025.empty:

        banklines_2025[
            banklines_2025["bank"] == bank
        ].plot(
            ax=ax,
            color="#222222",
            linewidth=1.5,
            alpha=0.85
        )

    # Plot each classification
    for classification in [
        "Retreat",
        "Advance",
        "Stable"
    ]:

        group = subset[
            subset["classification"] == classification
        ]

        if group.empty:
            continue

        sizes = (
            35
            + group["retreat_m"].abs()
            / max(mapped["retreat_m"].abs().max(), 1)
            * 120
        )

        ax.scatter(
            group.geometry.x,
            group.geometry.y,
            s=sizes,
            color=class_colors[classification],
            edgecolor="black",
            linewidth=0.7,
            alpha=0.9,
            label=classification,
            zorder=5
        )

    # Label retreat locations
    retreat_points = subset[
        subset["classification"] == "Retreat"
    ]

    for _, row in retreat_points.iterrows():

        ax.annotate(
            row["transect_id"],
            (
                row.geometry.x,
                row.geometry.y
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            weight="bold"
        )

    # Label strongest advance locations
    strongest_advance = subset[
        subset["classification"] == "Advance"
    ].nsmallest(
        3,
        "retreat_m"
    )

    for _, row in strongest_advance.iterrows():

        ax.annotate(
            row["transect_id"],
            (
                row.geometry.x,
                row.geometry.y
            ),
            xytext=(5, -10),
            textcoords="offset points",
            fontsize=8,
            weight="bold"
        )

    ax.set_title(
        bank_names[bank],
        fontsize=14,
        weight="bold"
    )

    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")

    ax.set_aspect("equal")

    ax.grid(
        alpha=0.2,
        linestyle="--"
    )


# ==========================================
# SHARED LEGEND
# ==========================================

legend_elements = [

    Line2D(
        [0], [0],
        marker="o",
        color="w",
        label="Retreat",
        markerfacecolor=class_colors["Retreat"],
        markeredgecolor="black",
        markersize=9
    ),

    Line2D(
        [0], [0],
        marker="o",
        color="w",
        label="Advance",
        markerfacecolor=class_colors["Advance"],
        markeredgecolor="black",
        markersize=9
    ),

    Line2D(
        [0], [0],
        marker="o",
        color="w",
        label="Stable",
        markerfacecolor=class_colors["Stable"],
        markeredgecolor="black",
        markersize=9
    )

]

fig.legend(
    handles=legend_elements,
    loc="lower center",
    ncol=3,
    frameon=True
)


fig.suptitle(
    "Historical Bank Erosion and Accretion Hotspots\n"
    "1990–2025 | Locations shown at 2025 bank positions",
    fontsize=16,
    weight="bold"
)

plt.tight_layout(
    rect=[0, 0.08, 1, 0.91]
)


# ==========================================
# SAVE MAP
# ==========================================

map_file = (
    MAP_DIR / "historical_erosion_hotspot_map.png"
)

plt.savefig(
    map_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==========================================
# HOTSPOT RANKING
# ==========================================

hotspots = mapped[
    mapped["classification"] == "Retreat"
].copy()

hotspots = hotspots.sort_values(
    "retreat_rate_m_per_year",
    ascending=False
)

hotspots["hotspot_rank"] = range(
    1,
    len(hotspots) + 1
)

hotspots.to_csv(
    REPORT_DIR / "historical_erosion_hotspot_ranking.csv",
    index=False
)


# ==========================================
# TERMINAL SUMMARY
# ==========================================

print("\n===== SPATIAL CLASSIFICATION SUMMARY =====")

print(
    mapped.groupby(
        ["bank", "classification"]
    ).size().unstack(
        fill_value=0
    ).to_string()
)


print("\n===== EROSION HOTSPOT RANKING =====")

if hotspots.empty:

    print("No retreat hotspots identified.")

else:

    print(
        hotspots[
            [
                "hotspot_rank",
                "transect_id",
                "bank",
                "retreat_m",
                "retreat_rate_m_per_year"
            ]
        ].round(2).to_string(index=False)
    )


print("\n===== OUTPUT FILES =====")

print(
    "- outputs/maps/historical_erosion_hotspot_map.png"
)

print(
    "- outputs/reports/erosion_hotspot_spatial_data.csv"
)

print(
    "- outputs/reports/historical_erosion_hotspot_ranking.csv"
)

print("\nStage 43 completed successfully.")
