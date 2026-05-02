# Silver Layer — Data Cleaning & Enrichment

The **Silver layer** transforms raw Bronze data into clean, enriched datasets ready for analysis.

---

## What Silver Does

```
Bronze (raw CSV)
    ↓
[Clean] nulls, types, duplicates
    ↓
[Enrich] postcode → ward/LSOA, demand signals
    ↓
[Output] CSV + Parquet (clean, normalized)
```

---

## Transformations Applied

### **1. Data Cleaning**

| Issue | Action |
|---|---|
| Null latitude/longitude | Drop row |
| Coordinates (0,0) | Drop row (invalid) |
| String lat/lng | Convert to float |
| Postcode format | Uppercase, trim whitespace |
| Duplicate chargeDeviceID | Keep first, drop rest |
| Complete row duplicates | Remove |

**Before:** 52,847 rows  
**After:** ~52,000 rows (minor cleaning)

---

### **2. Geo-Enrichment**

Join charger locations to ward/LSOA data using postcode prefix matching:

```
charger (postcode="BS10 1AA")
    ↓ extract prefix "BS10"
    ↓ join to wards table
charger + ward_name, lsoa_code, local_authority, population
```

**New columns:**
- `ward_name` — Which ward is this charger in?
- `lsoa_code` — Lower Super Output Area code
- `local_authority` — Bristol, South Glos, etc.
- `population` — Ward population (for density proxy)

---

### **3. Feature Engineering**

Add demand signal features for the Site Priority Score:

| Feature | Meaning | Used For |
|---|---|---|
| `population_nearby` | Ward population | Demand signal |
| `ev_adoption_rate` | EVs per capita (ward) | Demand proxy |
| `distance_to_motorway_km` | Distance to major road | Accessibility score |
| `is_urban` | Population > 10,000? | Segment (urban vs rural) |

---

## Data Quality Checks

Post-transformation validation:

```
[silver_validation.py] (built in Part 3)
  ✓ No null coordinates
  ✓ Coordinates in UK bounds
  ✓ Postcode format valid
  ✓ All wards matched (or noted as Unknown)
  ✓ Feature values in expected ranges
```

---

## Why This Matters

**Silver is the "single source of truth" for analytics.**

- ✅ Cleaned once, reused everywhere
- ✅ Null handling documented
- ✅ Derived features consistent
- ✅ Audit trail (Bronze → Silver transformation logged)
- ✅ Ready for Gold layer modelling

In production, this pattern prevents the "five different versions of the same dataset" problem.

---

## Output Files

```
data/silver/
└── 2026-05-02_ncr_chargers_silver.csv      (human-inspectable)
└── 2026-05-02_ncr_chargers_silver.parquet  (fast, for analytics)
```

Both files contain identical data. Use CSV for inspection, Parquet for analysis.

---

## Next: Gold Layer (Part 3)

Silver → Gold adds:

- ✅ Star schema (fact + dimension tables)
- ✅ KPI calculations (uptime %, utilization, etc.)
- ✅ Site Priority Score (the decision model)
- ✅ Ready for Power BI
