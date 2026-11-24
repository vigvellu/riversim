
import geopandas as gpd
import plotly.graph_objects as go
from pathlib import Path

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("outputs/maps")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

banks = gpd.read_file(DATA_DIR / "banklines.gpkg")
water = gpd.read_file(DATA_DIR / "water_polygons.gpkg")
transects = gpd.read_file(DATA_DIR / "transects.gpkg")

years = sorted(banks["year"].unique())

fig = go.Figure()

# Water polygons
for year in years:
    subset = water[water["year"] == year]

    for geometry in subset.geometry:
        if geometry.geom_type == "Polygon":
            x, y = geometry.exterior.xy
            fig.add_trace(go.Scatter(
                x=list(x),
                y=list(y),
                mode="lines",
                fill="toself",
                fillcolor="rgba(50, 130, 220, 0.10)",
                line=dict(color="rgba(50, 130, 220, 0.5)"),
                name=f"{year} water",
                legendgroup=str(year),
                visible=(year == years[0])
            ))

# Banklines
for year in years:
    for bank in ["north", "south"]:
        subset = banks[
            (banks["year"] == year) &
            (banks["bank"] == bank)
        ]

        for geometry in subset.geometry:
            x, y = geometry.xy

            fig.add_trace(go.Scatter(
                x=list(x),
                y=list(y),
                mode="lines",
                line=dict(
                    width=3,
                    dash="solid" if bank == "north" else "dash"
                ),
                name=f"{year} {bank} bank",
                legendgroup=str(year),
                visible=(year == years[0])
            ))

# Transects
for geometry in transects.geometry:
    x, y = geometry.xy
    fig.add_trace(go.Scatter(
        x=list(x),
        y=list(y),
        mode="lines",
        line=dict(color="grey", width=0.5),
        name="Transects",
        visible=True,
        showlegend=False
    ))

# Create year selector
buttons = []

# Number of traces per year:
# water polygons can vary in count, so track their actual traces.
trace_years = []

for year in years:
    trace_years.extend(
        [year] * len(water[water["year"] == year])
    )
    trace_years.extend([year] * 2)

# Transects are always visible
transect_count = len(transects)

for year in years:
    visibility = []

    for trace_year in trace_years:
        visibility.append(trace_year == year)

    visibility.extend([True] * transect_count)

    buttons.append(dict(
        label=str(year),
        method="update",
        args=[
            {"visible": visibility},
            {"title": f"Padma River Historical Comparison — {year}"}
        ]
    ))

fig.update_layout(
    title=f"Padma River Historical Comparison — {years[0]}",
    xaxis_title="Easting (m)",
    yaxis_title="Northing (m)",
    template="plotly_white",
    height=750,
    yaxis=dict(scaleanchor="x", scaleratio=1),
    updatemenus=[dict(
        buttons=buttons,
        direction="right",
        x=0.1,
        y=1.12,
        showactive=True
    )],
    legend_title="Map layers"
)

output_path = OUTPUT_DIR / "interactive_historical_map.html"
fig.write_html(output_path, auto_open=True)

print(f"\nInteractive map saved to: {output_path}")
