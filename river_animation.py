
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

frames = []

for year in years:

    traces = []

    # Water polygons
    yearly_water = water[water["year"] == year]

    for geometry in yearly_water.geometry:

        if geometry.geom_type == "Polygon":

            x, y = geometry.exterior.xy

            traces.append(
                go.Scatter(
                    x=list(x),
                    y=list(y),
                    mode="lines",
                    fill="toself",
                    fillcolor="rgba(50,130,220,0.15)",
                    line=dict(color="royalblue", width=1),
                    name="Water polygon"
                )
            )

    # North and south banklines
    for bank in ["north", "south"]:

        subset = banks[
            (banks["year"] == year) &
            (banks["bank"] == bank)
        ]

        for geometry in subset.geometry:

            x, y = geometry.xy

            traces.append(
                go.Scatter(
                    x=list(x),
                    y=list(y),
                    mode="lines",
                    line=dict(
                        color="red" if bank == "north" else "green",
                        width=3,
                        dash="solid" if bank == "north" else "dash"
                    ),
                    name=f"{bank.title()} bank"
                )
            )

    # Transects
    for geometry in transects.geometry:

        x, y = geometry.xy

        traces.append(
            go.Scatter(
                x=list(x),
                y=list(y),
                mode="lines",
                line=dict(color="grey", width=0.5),
                name="Transects",
                showlegend=False
            )
        )

    frames.append(
        go.Frame(
            data=traces,
            name=str(year),
            layout=go.Layout(
                title=f"Padma River Channel Evolution — {year}"
            )
        )
    )

# Initialize using the first year
fig = go.Figure(
    data=frames[0].data,
    frames=frames
)

fig.update_layout(
    title=f"Padma River Channel Evolution — {years[0]}",
    xaxis_title="Easting (m)",
    yaxis_title="Northing (m)",
    template="plotly_white",
    height=750,
    yaxis=dict(
        scaleanchor="x",
        scaleratio=1
    ),
    updatemenus=[
        dict(
            type="buttons",
            showactive=False,
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[
                        None,
                        {
                            "frame": {"duration": 1200, "redraw": True},
                            "fromcurrent": True
                        }
                    ]
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[
                        [None],
                        {
                            "frame": {"duration": 0, "redraw": False},
                            "mode": "immediate"
                        }
                    ]
                )
            ]
        )
    ],
    sliders=[
        dict(
            steps=[
                dict(
                    method="animate",
                    args=[
                        [str(year)],
                        {
                            "frame": {"duration": 500, "redraw": True},
                            "mode": "immediate"
                        }
                    ],
                    label=str(year)
                )
                for year in years
            ],
            active=0
        )
    ]
)

output_path = OUTPUT_DIR / "river_evolution_animation.html"

fig.write_html(
    output_path,
    auto_open=True
)

print("\nAnimation created successfully!")
print(f"Saved to: {output_path}")
