
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

REPORT_DIR = Path("outputs/reports")
GRAPH_DIR = Path("outputs/graphs")

INPUT_FILE = REPORT_DIR / "erosion_accretion_results.csv"
MASTER_REPORT = REPORT_DIR / "riversim_historical_report.txt"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1990
END_YEAR = 2025
DURATION = END_YEAR - START_YEAR

print("\nRIVERSIM — EROSION & ACCRETION INTEGRATION")


# ==========================================
# LOAD DATA
# ==========================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Missing input file: {INPUT_FILE}"
    )

data = pd.read_csv(INPUT_FILE)

print("\n===== INPUT DATA =====")
print(f"Records loaded: {len(data)}")


# ==========================================
# VALIDATE DATA
# ==========================================

required_columns = {
    "transect_id",
    "bank",
    "displacement_m",
    "retreat_m",
    "retreat_rate_m_per_year",
    "classification"
}

missing = required_columns - set(data.columns)

if missing:
    raise ValueError(
        f"Missing columns: {sorted(missing)}"
    )

if len(data) != 38:
    print(
        f"WARNING: Expected 38 records, found {len(data)}"
    )

if not set(data["bank"].unique()).issubset(
    {"north", "south"}
):
    raise ValueError("Unexpected bank values found.")

if not set(data["classification"].unique()).issubset(
    {"Retreat", "Advance", "Stable"}
):
    raise ValueError("Unexpected classification values found.")

# Check whether the signed values agree with classifications.
invalid_signs = (
    ((data["classification"] == "Retreat") &
     (data["retreat_m"] <= 0))
    |
    ((data["classification"] == "Advance") &
     (data["retreat_m"] >= 0))
    |
    ((data["classification"] == "Stable") &
     (data["retreat_m"] != 0))
)

if invalid_signs.any():
    raise ValueError(
        "Some retreat/accretion signs do not match classifications."
    )

print("Data validation completed.")


# ==========================================
# ADD STUDY PERIOD
# ==========================================

data["start_year"] = START_YEAR
data["end_year"] = END_YEAR
data["duration_years"] = DURATION


# ==========================================
# BANK-SPECIFIC SUMMARY
# ==========================================

summary = data.groupby("bank").agg(

    transect_count=(
        "transect_id",
        "nunique"
    ),

    mean_signed_retreat_m=(
        "retreat_m",
        "mean"
    ),

    median_signed_retreat_m=(
        "retreat_m",
        "median"
    ),

    mean_signed_rate_m_per_year=(
        "retreat_rate_m_per_year",
        "mean"
    ),

    maximum_retreat_m=(
        "retreat_m",
        "max"
    ),

    maximum_advance_m=(
        "retreat_m",
        "min"
    ),

    mean_absolute_displacement_m=(
        "displacement_m",
        lambda x: x.abs().mean()
    )

).reset_index()


# ==========================================
# CLASSIFICATION COUNTS
# ==========================================

classification_counts = pd.crosstab(
    data["bank"],
    data["classification"]
)

for classification in [
    "Retreat",
    "Advance",
    "Stable"
]:

    if classification not in classification_counts.columns:
        classification_counts[classification] = 0

classification_counts = classification_counts[
    ["Retreat", "Advance", "Stable"]
]

classification_counts = classification_counts.reset_index()


summary = summary.merge(
    classification_counts,
    on="bank",
    how="left"
)


# ==========================================
# SAVE BANK SUMMARY
# ==========================================

summary_file = (
    REPORT_DIR / "erosion_accretion_bank_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)


# ==========================================
# TRANSECT-LEVEL RESULTS
# ==========================================

detailed = data.sort_values(
    ["bank", "transect_id"]
).copy()

detailed.to_csv(
    REPORT_DIR / "erosion_accretion_by_transect.csv",
    index=False
)


# ==========================================
# EROSION HOTSPOT IDENTIFICATION
# ==========================================

hotspots = data[
    data["classification"] == "Retreat"
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
    REPORT_DIR / "erosion_hotspots_1990_2025.csv",
    index=False
)


# ==========================================
# ACCRETION / ADVANCE LOCATIONS
# ==========================================

advance = data[
    data["classification"] == "Advance"
].copy()

advance = advance.sort_values(
    "retreat_rate_m_per_year"
)

advance.to_csv(
    REPORT_DIR / "bank_advance_locations_1990_2025.csv",
    index=False
)


# ==========================================
# GRAPH 1 — CLASSIFICATION COUNTS
# ==========================================

plot_data = classification_counts.set_index("bank")

plot_data = plot_data[
    ["Retreat", "Advance", "Stable"]
]

ax = plot_data.plot(
    kind="bar",
    figsize=(10, 6),
    width=0.7
)

ax.set_title(
    "Bank Erosion and Accretion Classification (1990–2025)"
)

ax.set_xlabel("River bank")
ax.set_ylabel("Number of transects")

ax.set_xticklabels(
    ["North", "South"],
    rotation=0
)

ax.grid(
    axis="y",
    alpha=0.3
)

ax.legend(
    title="Classification"
)

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "erosion_accretion_classification.png",
    dpi=300
)

plt.close()


# ==========================================
# GRAPH 2 — SIGNED RETREAT RATES
# ==========================================

fig, ax = plt.subplots(figsize=(13, 6))

for bank in ["north", "south"]:

    subset = data[
        data["bank"] == bank
    ].sort_values("transect_id")

    ax.plot(
        subset["transect_id"],
        subset["retreat_rate_m_per_year"],
        marker="o",
        label=bank.capitalize()
    )

ax.axhline(0, linewidth=1)

ax.set_title(
    "Transect-Level Bank Retreat and Advance Rates (1990–2025)"
)

ax.set_xlabel("Transect")
ax.set_ylabel("Signed rate (m/year)")

ax.grid(alpha=0.3)

ax.legend()

plt.tight_layout()

plt.savefig(
    GRAPH_DIR / "erosion_accretion_transect_rates.png",
    dpi=300
)

plt.close()


# ==========================================
# UPDATE CONSOLIDATED TEXT REPORT
# ==========================================

marker = "EROSION AND ACCRETION ANALYSIS"

if MASTER_REPORT.exists():

    existing_report = MASTER_REPORT.read_text(
        encoding="utf-8"
    )

    # Remove an earlier version of this section if rerunning.
    if marker in existing_report:
        existing_report = existing_report.split(
            marker
        )[0].rstrip()

else:

    existing_report = (
        "RIVERSIM\n"
        "CONSOLIDATED HISTORICAL CHANGE REPORT\n"
    )


report_lines = [

    marker,

    f"Study period: {START_YEAR}–{END_YEAR}",

    f"Duration: {DURATION} years",

    "",

    "Sign convention:",

    "Positive retreat_m = landward retreat.",

    "Negative retreat_m = channelward advance.",

    "Zero retreat_m = stable.",

    "",

    "BANK SUMMARY",

    ""
]


for _, row in summary.iterrows():

    report_lines.extend([

        f"Bank: {row['bank'].capitalize()}",

        f"Transects: {int(row['transect_count'])}",

        f"Retreat classifications: {int(row['Retreat'])}",

        f"Advance classifications: {int(row['Advance'])}",

        f"Stable classifications: {int(row['Stable'])}",

        f"Mean signed retreat: "
        f"{row['mean_signed_retreat_m']:.2f} m",

        f"Mean signed rate: "
        f"{row['mean_signed_rate_m_per_year']:.2f} m/year",

        f"Maximum retreat: "
        f"{row['maximum_retreat_m']:.2f} m",

        f"Maximum advance (signed): "
        f"{row['maximum_advance_m']:.2f} m",

        ""

    ])


report_lines.extend([

    "RETREAT HOTSPOTS",

    ""
])


if hotspots.empty:

    report_lines.append(
        "No retreat hotspots identified."
    )

else:

    for _, row in hotspots.iterrows():

        report_lines.append(

            f"Rank {int(row['hotspot_rank'])}: "
            f"{row['transect_id']} "
            f"({row['bank']}) — "
            f"{row['retreat_m']:.2f} m retreat, "
            f"{row['retreat_rate_m_per_year']:.2f} m/year"

        )


report_lines.extend([

    "",

    "LIMITATIONS",

    "These results are based on digitized bank positions.",

    "They are provisional and require validation against",

    "original satellite imagery and independent reference data.",

    "",

    "END OF EROSION AND ACCRETION SECTION"

])


updated_report = (
    existing_report
    + "\n\n"
    + "\n".join(report_lines)
    + "\n"
)

MASTER_REPORT.write_text(
    updated_report,
    encoding="utf-8"
)


# ==========================================
# TERMINAL OUTPUT
# ==========================================

print("\n===== BANK SUMMARY =====")

print(
    summary.round(2).to_string(index=False)
)


print("\n===== EROSION HOTSPOTS =====")

if hotspots.empty:

    print("No retreat hotspots found.")

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


print("\n===== ADVANCE LOCATIONS =====")

print(
    advance[
        [
            "transect_id",
            "bank",
            "retreat_m",
            "retreat_rate_m_per_year"
        ]
    ].round(2).to_string(index=False)
)


# ==========================================
# OUTPUT FILES
# ==========================================

print("\n===== FILES CREATED =====")

output_files = [

    REPORT_DIR / "erosion_accretion_bank_summary.csv",

    REPORT_DIR / "erosion_accretion_by_transect.csv",

    REPORT_DIR / "erosion_hotspots_1990_2025.csv",

    REPORT_DIR / "bank_advance_locations_1990_2025.csv",

    MASTER_REPORT,

    GRAPH_DIR / "erosion_accretion_classification.png",

    GRAPH_DIR / "erosion_accretion_transect_rates.png"

]

for file in output_files:

    print(f"- {file}")


print("\nStage 42 completed successfully.")
