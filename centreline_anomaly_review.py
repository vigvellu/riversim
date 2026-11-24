import pandas as pd
from pathlib import Path

output = Path("outputs/reports")
output.mkdir(parents=True, exist_ok=True)

reviews = pd.DataFrame([
    {
        "year": 2015,
        "transect_pair": "T02-T03",
        "anomalous_bank": "south",
        "visual_review": "Natural",
        "decision": "Retain provisionally"
    },
    {
        "year": 2015,
        "transect_pair": "T18-T19",
        "anomalous_bank": "north",
        "visual_review": "Natural",
        "decision": "Retain provisionally"
    },
    {
        "year": 2025,
        "transect_pair": "T18-T19",
        "anomalous_bank": "south",
        "visual_review": "Natural",
        "decision": "Retain provisionally"
    }
])

reviews.to_csv(
    output / "centreline_anomaly_review.csv",
    index=False
)

print("\n===== CENTRELINE ANOMALY REVIEW =====")
print(reviews.to_string(index=False))

print("\nReview saved successfully.")