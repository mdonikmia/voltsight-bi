"""
Silver layer transformation logic.

This module handles:
  1. Reading Bronze raw data
  2. Cleaning (nulls, types, duplicates)
  3. Geo-enrichment (postcode → ward/LSOA)
  4. Feature engineering (demand signals, motorway proximity, etc.)
  5. Writing to Silver as clean parquet

The Silver layer is the "single source of truth" for analytical work.
Every transform here is documented and can be reversed if needed.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from voltsight.logger import get_logger

log = get_logger(__name__)


def create_synthetic_ward_mapping(n_wards: int = 500) -> pd.DataFrame:
    """
    Create a synthetic postcode → ward mapping.

    In a real project, this would come from ONS Open Geography Portal.
    For this portfolio project, we generate realistic synthetic data.

    Returns:
        DataFrame with columns: postcode_prefix, ward_name, lsoa_code,
                               local_authority, latitude, longitude, population
    """
    np.random.seed(42)  # Reproducible

    ward_data = []
    for i in range(n_wards):
        # FIXED: Use unique postcode prefixes (BS0-BS499, not BS0-BS98 repeated)
        postcode_prefix = f"BS{i}"
        ward_name = f"Ward_{i % 50}"
        lsoa = f"E01{i:06d}"
        la = "Bristol" if i % 2 == 0 else "South Gloucestershire"
        lat = 51.45 + np.random.normal(0, 0.05)
        lng = -2.58 + np.random.normal(0, 0.05)
        pop = int(np.random.uniform(5000, 15000))

        ward_data.append({
            "postcode_prefix": postcode_prefix,
            "ward_name": ward_name,
            "lsoa_code": lsoa,
            "local_authority": la,
            "ward_latitude": lat,
            "ward_longitude": lng,
            "population": pop,
        })

    return pd.DataFrame(ward_data)


def clean_charger_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize charger data from Bronze.

    Transformations:
      - Convert lat/lng to float (handle string inputs)
      - Uppercase postcode
      - Remove rows with null latitude/longitude
      - Remove complete duplicates
      - Drop rows with invalid (0,0) coordinates
      - Type casting for all columns

    Args:
        df: Raw Bronze charger DataFrame

    Returns:
        Cleaned DataFrame ready for enrichment
    """
    log.info(f"Cleaning {len(df):,} charger records")

    # Copy to avoid modifying original
    df = df.copy()

    # Type casting
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Standardize postcode
    if "postcode" in df.columns:
        df["postcode"] = df["postcode"].str.upper().str.strip()

    # Remove null coordinates
    before_null = len(df)
    df = df.dropna(subset=["latitude", "longitude"])
    log.info(f"Removed {before_null - len(df)} rows with null coordinates")

    # Remove (0,0) coordinates (invalid)
    before_zero = len(df)
    df = df[(df["latitude"] != 0.0) | (df["longitude"] != 0.0)]
    log.info(f"Removed {before_zero - len(df)} rows with (0,0) coordinates")

    # Remove complete duplicates
    before_dup = len(df)
    df = df.drop_duplicates()
    log.info(f"Removed {before_dup - len(df)} complete duplicate rows")

    # Remove duplicates on chargeDeviceID (keep first occurrence)
    if "chargeDeviceID" in df.columns:
        before_id_dup = len(df)
        df = df.drop_duplicates(subset=["chargeDeviceID"], keep="first")
        log.info(
            f"Removed {before_id_dup - len(df)} duplicate chargeDeviceIDs"
        )

    log.info(f"After cleaning: {len(df):,} records")
    return df


def extract_postcode_prefix(postcode: str) -> str:
    """
    Extract postcode prefix (e.g., 'BS10' from 'BS10 1AA').

    UK postcodes have format: OUTWARD INWARD
    Outward = 1-2 letters + 1-2 digits
    Inward = 1 digit + 2 letters
    """
    if pd.isna(postcode):
        return None
    # Split on space and take first part (outward code)
    parts = str(postcode).split()
    return parts[0] if parts else None


def enrich_with_geography(
    chargers: pd.DataFrame,
    wards: pd.DataFrame,
) -> pd.DataFrame:
    """
    Enrich charger data with geographic/demographic features.

    Join on postcode prefix → ward, then add derived features:
      - Ward name, LSOA, local authority
      - Population density proxy
      - Distance to nearest motorway (simulated)
      - EV adoption rate by ward (simulated demand signal)

    Args:
        chargers: Cleaned charger DataFrame
        wards: Ward mapping DataFrame (from ONS or synthetic)

    Returns:
        Enriched charger DataFrame with geographic features
    """
    log.info("Enriching chargers with geographic data")

    chargers = chargers.copy()

    # Extract postcode prefix for joining
    chargers["postcode_prefix"] = chargers["postcode"].apply(
        extract_postcode_prefix
    )

    # Left join on postcode prefix
    chargers = chargers.merge(
        wards,
        on="postcode_prefix",
        how="left",
    )

    # For unmatched chargers, fill with defaults
    chargers["ward_name"] = chargers["ward_name"].fillna("Unknown")
    chargers["lsoa_code"] = chargers["lsoa_code"].fillna("Unknown")
    chargers["local_authority"] = chargers["local_authority"].fillna(
        "Unknown"
    )

    log.info(f"Joined {chargers['ward_name'].notna().sum():,} chargers to wards")

    return chargers


def add_demand_features(chargers: pd.DataFrame) -> pd.DataFrame:
    """
    Add demand signal features for the Site Priority Score.

    Features:
      - population_nearby: population in the charger's ward
      - ev_adoption_rate: EV registrations per capita by ward (simulated)
      - distance_to_motorway_km: proximity to major road (simulated)
      - urban_flag: is this an urban area? (population > 10k)

    These are used later in the Site Priority Score calculation.
    """
    log.info("Adding demand signal features")

    chargers = chargers.copy()

    # Population-based features
    chargers["population_nearby"] = chargers["population"].fillna(8000)

    # EV adoption: simulated as random but correlated with population
    np.random.seed(42)
    chargers["ev_adoption_rate"] = (
        (chargers["population_nearby"] / 10000) * np.random.uniform(0.02, 0.08, len(chargers))
    )

    # Distance to motorway: simulated based on latitude
    # (chargers at certain latitudes are closer to motorways)
    chargers["distance_to_motorway_km"] = 5 + (
        (chargers["latitude"] - 51.5).abs() * 10
    ).clip(lower=0.5, upper=20)

    # Urban flag
    chargers["is_urban"] = chargers["population_nearby"] > 10000

    log.info("Added demand features")
    return chargers


def transform_bronze_to_silver(
    bronze_dir: Path,
    silver_dir: Path,
) -> dict[str, Path]:
    """
    Full transformation pipeline: Bronze → Silver.

    Orchestrates:
      1. Read Bronze charger CSV
      2. Create synthetic ward mapping
      3. Clean charger data
      4. Geo-enrich with wards
      5. Add demand features
      6. Write to Silver (CSV + Parquet)

    Args:
        bronze_dir: Path to bronze/ncr_chargers/ folder
        silver_dir: Path to silver/ folder (created if missing)

    Returns:
        Dict mapping output format to file path
    """
    log.info("=" * 60)
    log.info("VoltSight BI — Bronze → Silver Transformation")
    log.info("=" * 60)

    # Create Silver directory
    silver_dir.mkdir(parents=True, exist_ok=True)

    # Read Bronze data (latest CSV)
    bronze_files = sorted(bronze_dir.glob("*.csv"))
    if not bronze_files:
        log.error(f"No CSV files found in {bronze_dir}")
        return {}

    latest_csv = bronze_files[-1]
    log.info(f"Reading {latest_csv.name}")
    chargers = pd.read_csv(latest_csv, low_memory=False)
    log.info(f"Loaded {len(chargers):,} chargers")

    # Transformation pipeline
    chargers = clean_charger_data(chargers)

    wards = create_synthetic_ward_mapping()
    chargers = enrich_with_geography(chargers, wards)

    chargers = add_demand_features(chargers)

    # Output files
    output_date = latest_csv.stem.split("_")[0]  # Extract YYYY-MM-DD
    csv_path = silver_dir / f"{output_date}_ncr_chargers_silver.csv"
    parquet_path = silver_dir / f"{output_date}_ncr_chargers_silver.parquet"

    chargers.to_csv(csv_path, index=False)
    log.info(f"Written {csv_path.name}")

    chargers.to_parquet(parquet_path, index=False, engine="pyarrow")
    log.info(f"Written {parquet_path.name}")

    log.info("=" * 60)
    log.info(f"Silver layer complete: {len(chargers):,} chargers ready")
    log.info("=" * 60)

    return {
        "csv": csv_path,
        "parquet": parquet_path,
    }