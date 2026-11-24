# RiverSim

**Historical River Morphology Analysis and Exploratory Scenario Simulator**  
Study area: Padma River, Rajshahi, Bangladesh  
Study period: 1990–2025  
CRS: EPSG:32645

## Overview

RiverSim is a Python/GIS project for analysing prepared historical riverbank and channel measurements. It includes bank migration calculations, channel-width and centre-position analysis, provisional erosion/accretion classification, approximate centreline reconstruction, spatial maps, data-quality screening, a Streamlit dashboard and rate-based exploratory scenarios.

> **Important:** Results are provisional. Internal geometry checks do not prove that the original bank positions are accurate. Validate measurements against original satellite imagery and, where possible, field observations before making scientific or engineering claims.

## Dataset

The current project contains:

- 228 bank-point features (19 transects × 2 banks × 6 years)
- 12 bankline features
- 19 transects
- 7 water polygons
- 6 reconstructed centreline features
- Observation years: 1990, 2000, 2010, 2015, 2020 and 2025

Spatial layers use EPSG:32645.

## Project layout

```text
riversim/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── outputs/
│   ├── graphs/
│   ├── maps/
│   └── reports/
├── src/
├── app.py
├── requirements.txt
└── analysis_scripts.py
```

## Environment setup

Use a supported Python version compatible with the packages in `requirements.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the virtual environment already exists, use its interpreter directly rather than relying on PowerShell activation.

## Run the dashboard

From the project root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run analysis scripts

Run scripts from the project root so relative paths resolve correctly:

```powershell
.\.venv\Scripts\python.exe validate_data.py
.\.venv\Scripts\python.exe migration_analysis.py
.\.venv\Scripts\python.exe migration_rates.py
.\.venv\Scripts\python.exe channel_analysis.py
.\.venv\Scripts\python.exe erosion_accretion.py
.\.venv\Scripts\python.exe data_quality_assessment.py
.\.venv\Scripts\python.exe historical_change_report.py
.\.venv\Scripts\python.exe erosion_hotspot_map.py
```

The scripts listed above represent the analysis workflow; preserve the original inputs and inspect outputs before running later stages.

## Main analyses

- Bank displacement, NSM and EPR
- Annualized migration rates by transect and interval
- Channel width and centre-position change
- Provisional erosion/accretion interpretation
- Approximate historical centreline reconstruction
- Spatial migration and erosion hotspot maps
- Data quality and uncertainty flags
- Exploratory constant-rate and transect-specific scenarios

## Important interpretation notes

1. Transect distance increases from the northeast/north toward the southwest/south.
2. Signed displacement must be interpreted with bank orientation.
3. Positive landward retreat and negative channelward advance are the adopted erosion/accretion convention.
4. Reconstructed centrelines connect transect midpoints; they are not independently extracted channel centrelines.
5. Scenario outputs are hypothetical extrapolations, not calibrated predictions.
6. Large changes and review flags must be checked against source imagery before being interpreted as physical river behaviour.

## Key outputs

See `outputs/reports/` for CSV and text reports, `outputs/graphs/` for plots and `outputs/maps/` for spatial figures. Important outputs include:

- `historical_change_master.csv`
- `erosion_accretion_bank_summary.csv`
- `historical_erosion_hotspot_ranking.csv`
- `data_quality_checks.csv`
- `data_quality_review_register.csv`
- `riversim_historical_report.txt`
- `riversim_data_quality_report.txt`
- `historical_all_years_overlay.png`
- `historical_erosion_hotspot_map.png`

## Limitations

The current workflow does not model hydraulics, sediment transport, bank-material failure, flood hydraulics or channel feedback. It does not establish causality. The source measurements and digitization should be independently validated before the project is used for formal engineering decisions.

## Citation

If using or presenting this project, describe it as an exploratory Python/GIS analysis of the supplied Padma River measurement dataset. Add author, department, institution, data-source citations and imagery acquisition details before submitting or publishing.
