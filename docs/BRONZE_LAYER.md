# Bronze Layer — Data Ingestion Documentation

This document explains the **Bronze layer** of VoltSight BI: what it contains, how it is structured, and the engineering decisions behind it.

---

## Purpose

The Bronze layer is the **immutable record of truth** for all external data entering VoltSight BI. Every byte of analysis downstream traces back to a file in this layer.

Three rules govern Bronze:

1. **Never modify raw data.** Files are read-only after ingestion.
2. **Never delete it.** Even when it looks wrong, you investigate; you don't overwrite.
3. **Always timestamp it.** Every file is prefixed with the pull date.

This is the same pattern used in production data lakes at major organisations — it makes data lineage auditable.

---

## What's in Bronze

| Source | Folder | Format | Description |
|---|---|---|---|
| UK National Chargepoint Registry | `ncr_chargers/` | CSV + Parquet | ~50k EV chargers across the UK with location, type, power, operator |
| ONS Postcode Directory | `ons_postcode_directory/` | CSV | UK postcode → ward / LSOA / local authority mapping |
| DVLA EV Registrations | `dvla_ev_registrations/` | CSV (manual) | Quarterly count of plug-in vehicles by local authority — the demand signal |

Each folder follows the same layout:

```
ncr_chargers/
├── 2026-05-02_ncr_chargers.csv          # Original download (immutable)
├── 2026-05-02_ncr_chargers.parquet      # Fast-loading copy (derived)
└── _manifest.json                        # Provenance record
```

---

## The Manifest File

Every source folder contains a `_manifest.json`. This is the **lineage record** for that source — answering "when did we pull this, from where, was it complete, did it change since last time?"

Example:

```json
{
  "source_key": "ncr_chargers",
  "source_name": "UK National Chargepoint Registry",
  "source_url": "https://chargepoints.dft.gov.uk/api/retrieve/registry/format/csv",
  "pull_timestamp_utc": "2026-05-02T14:23:11Z",
  "filename": "2026-05-02_ncr_chargers.csv",
  "file_size_bytes": 18472913,
  "file_sha256": "a7c2...e419",
  "row_count": 52847,
  "license": "Open Government Licence v3.0",
  "schema_version": "1.0",
  "notes": ""
}
```

The SHA256 hash means we can verify file integrity over time and detect whether a re-download produced different content.

---

## Engineering Decisions Explained

These are choices a senior reviewer would expect to see justified:

**Why both CSV and Parquet?**
CSV is human-readable and directly inspectable in any text editor — useful for debugging. Parquet is a compressed columnar format that pandas reads 5–10× faster than CSV and preserves data types. Downstream Silver code reads parquet by default; CSV is the fallback and the lineage anchor.

**Why a manifest file?**
Data lineage. When a number on the dashboard looks wrong six months from now, the manifest answers "where did this come from, and when?" — without it, every investigation starts from zero.

**Why date-prefixed filenames?**
You always know the freshness of the data without opening a file. Sorting alphabetically gives you chronological order. Re-running ingestion on a new day creates a new file alongside the old one — history is preserved.

**Why retry logic with exponential backoff?**
Government APIs (DfT, ONS) experience transient failures, especially under load. A naive script crashes on the first 503 response. Production-grade ingestion assumes failure and retries with increasing delays — the pattern used by every robust data pipeline.

**Why idempotency?**
The ingestion script can be safely re-run any number of times on the same day without re-downloading or corrupting state. This is critical when integrating into a scheduler (cron, Airflow) — failures and re-runs are normal operations.

**Why fail-soft (one source failing doesn't block others)?**
Independent sources should fail independently. If DVLA's site is down, NCR ingestion should still complete. Each source has its own try/except boundary.

---

## Running the Bronze Layer

### First-time setup

```bash
# Install dependencies
pip install -r requirements.txt
```

### Run ingestion

```bash
# Pull all sources
python scripts/ingest_bronze.py

# Pull only one source (for debugging)
python scripts/ingest_bronze.py --source ncr_chargers
```

### Validate quality

```bash
python scripts/validate_bronze.py
```

The validator exits with code 0 if all checks pass. Use this in CI pipelines (GitHub Actions) to gate Silver-layer promotion.

### Run unit tests

```bash
pytest tests/ -v
```

---

## Validation Checks (NCR Chargers)

The following checks run against the NCR data after every pull:

| Check | What it verifies |
|---|---|
| `manifest_exists` | A `_manifest.json` was written |
| `data_file_exists` | The CSV/Parquet file is on disk |
| `row_count_above_30k` | At least 30k rows — sanity check; UK has ~50k chargers |
| `required_columns_present` | `chargeDeviceID`, `latitude`, `longitude`, `postcode` all exist |
| `latitudes_in_uk_range` | ≥95% of latitudes between 49.0 and 61.0 |
| `longitudes_in_uk_range` | ≥95% of longitudes between -8.5 and 2.0 |
| `postcodes_present` | ≥85% of records have a postcode value |
| `no_complete_duplicates` | No row appears twice identically |

Failing these does **not** delete the data — it surfaces the issue for investigation. Bronze data is preserved even if invalid; Silver is where dirty data gets cleaned or rejected.

---

## What Happens Next

Once Bronze passes validation, the **Silver layer** picks up these files and transforms them: null handling, type casting, deduplication, geo-enrichment (joining chargers to wards/LSOAs by postcode). Silver is covered in the next document.

---

## Manual Steps Required

The DVLA EV registrations source does not provide a stable direct download URL. After running `ingest_bronze.py`, manually download the latest VEH0145 file from:

> https://www.gov.uk/government/statistical-data-sets/vehicle-licensing-statistics-data-files

Save it as `data/bronze/dvla_ev_registrations/<YYYY-MM-DD>_dvla_veh0145_ulev_by_la.csv` and re-run validation.

This is documented in `config/sources.yaml` under the `notes` field for transparency.
