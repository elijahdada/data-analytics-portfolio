import pandas as pd
import numpy as np
from pathlib import Path

# Reproducibility
np.random.seed(42)

# Project directories
PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

counties = [
    "Bomi", "Bong", "Gbarpolu", "Grand Bassa", "Grand Cape Mount",
    "Grand Gedeh", "Grand Kru", "Lofa", "Margibi", "Maryland",
    "Montserrado", "Nimba", "River Cess", "River Gee", "Sinoe"
]

# Size of each facility type, used to scale targets
type_scale = {"Hospital": 1.5, "Health Center": 1.0, "Clinic": 0.6}

# ---------- 1. Facility master ----------
facilities = []
for c_idx, county in enumerate(counties, start=1):
    for i in range(1, 3):
        facilities.append({
            "facility_id": f"C{c_idx:02d}-F{i}",
            "facility_name": f"{county} Health Facility {i}",
            "county": county,
            "facility_type": np.random.choice(list(type_scale.keys()))
        })
facility_df = pd.DataFrame(facilities)

# ---------- 2. Monthly programme data ----------
months = pd.date_range("2026-01-01", periods=12, freq="MS")
rows = []
for _, fac in facility_df.iterrows():
    scale = type_scale[fac["facility_type"]]
    fp_target = int(round(120 * scale))
    adol_target = int(round(60 * scale))
    gbv_target = max(1, int(round(8 * scale)))

    for m_idx, month in enumerate(months):
        trend = 0.85 + 0.015 * m_idx   # gradual improvement over the year
        rows.append({
            "reporting_month": month.strftime("%Y-%m"),
            "county": fac["county"],
            "facility_id": fac["facility_id"],
            "fp_clients": max(0, int(np.random.normal(fp_target * trend, fp_target * 0.12))),
            "adolescent_clients": max(0, int(np.random.normal(adol_target * trend, adol_target * 0.15))),
            "gbv_referrals": int(np.random.poisson(gbv_target * trend)),
            "facilities_reporting": 1,
            "fp_target": fp_target,
            "adolescent_target": adol_target,
            "gbv_target": gbv_target
        })

monthly_df = pd.DataFrame(rows)

# Simulate 15 missing reports (no data submitted)
gap_idx = np.random.choice(monthly_df.index, size=15, replace=False)
monthly_df.loc[gap_idx, "facilities_reporting"] = 0
monthly_df.loc[gap_idx, ["fp_clients", "adolescent_clients", "gbv_referrals"]] = np.nan

# ---------- 3. Indicator targets ----------
targets_df = pd.DataFrame({
    "indicator": [
        "Family planning clients", "Adolescents accessing SRHR services",
        "GBV cases referred", "Facilities reporting",
        "Reports submitted on time", "Programme targets achieved"
    ],
    "definition": [
        "Number of clients receiving family planning services",
        "Number of adolescents accessing SRHR services",
        "Number of GBV cases referred for support",
        "Number of health facilities submitting a monthly report",
        "Percentage of facilities submitting reports on time",
        "Percentage of programme targets achieved"
    ],
    "annual_target": [
        int(monthly_df.groupby("facility_id")["fp_target"].first().sum() * 12),
        int(monthly_df.groupby("facility_id")["adolescent_target"].first().sum() * 12),
        int(monthly_df.groupby("facility_id")["gbv_target"].first().sum() * 12),
        30, 90, 100
    ]
})

# ---------- Save ----------
facility_df.to_csv(RAW_DIR / "facility_master.csv", index=False)
monthly_df.to_csv(RAW_DIR / "monthly_program_data.csv", index=False)
targets_df.to_csv(RAW_DIR / "indicator_targets.csv", index=False)

print("DATA GENERATION COMPLETED")
print("-" * 32)
print(f"Counties: {facility_df['county'].nunique()}")
print(f"Facilities: {len(facility_df)}")
print(f"Monthly records: {len(monthly_df)}")
print(f"Reporting gaps: {(monthly_df['facilities_reporting'] == 0).sum()}")
