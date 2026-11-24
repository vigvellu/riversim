
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

OUTPUT_DIR = Path("outputs")
REPORT_DIR = OUTPUT_DIR / "reports"
GRAPH_DIR = OUTPUT_DIR / "graphs"

rates = pd.read_csv(REPORT_DIR / "migration_rates.csv")

# Create readable period labels
rates["period"] = (
    rates["start_year"].astype(str)
    + "-"
    + rates["end_year"].astype(str)
)

period_order = [
    "1990-2000",
    "2000-2010",
    "2010-2015",
    "2015-2020",
    "2020-2025"
]

# Create separate heatmaps for each bank
fig, axes = plt.subplots(
    2, 1,
    figsize=(13, 12)
)

for ax, bank in zip(axes, ["north", "south"]):

    data = rates[rates["bank"] == bank]

    heatmap_data = data.pivot(
        index="transect_id",
        columns="period",
        values="migration_rate_m_per_year"
    )

    heatmap_data = heatmap_data.reindex(
        index=[f"T{i:02d}" for i in range(1, 20)],
        columns=period_order
    )

    values = heatmap_data.values

    # Center the color scale around zero
    limit = abs(values).max()

    norm = TwoSlopeNorm(
        vmin=-limit,
        vcenter=0,
        vmax=limit
    )

    image = ax.imshow(
        values,
        cmap="RdYlBu_r",
        aspect="auto",
        norm=norm
    )

    # Add values inside cells
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):

            ax.text(
                j, i,
                f"{values[i, j]:.0f}",
                ha="center",
                va="center",
                fontsize=8
            )

    ax.set_title(f"{bank.title()} Bank")
    ax.set_xticks(range(len(period_order)))
    ax.set_xticklabels(period_order)
    ax.set_yticks(range(19))
    ax.set_yticklabels(heatmap_data.index)

    ax.set_xlabel("Observation period")
    ax.set_ylabel("Transect")

    fig.colorbar(
        image,
        ax=ax,
        label="Migration rate (m/year)"
    )

plt.suptitle(
    "Padma River: Bank Migration Rate Heatmaps",
    fontsize=16
)

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "migration_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Heatmap generated successfully!")
print("Saved: outputs/graphs/migration_heatmap.png")
