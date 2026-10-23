# utils/data_loader.py — Safe data loading with integrity checks
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    HOTSPOT_EVENTS_PATH, HOTSPOT_AGG_PATH, JOINED_TABLE_PATH,
    EXPECTED_TOTAL_HOTSPOTS, MONTH_LABELS
)

_cache = {}

def load_hotspot_events() -> pd.DataFrame:
    """Load event-level hotspot data (8,606 rows)."""
    if "events" not in _cache:
        df = pd.read_parquet(HOTSPOT_EVENTS_PATH)
        # Integrity check
        assert len(df) == EXPECTED_TOTAL_HOTSPOTS, (
            f"Hotspot events count mismatch: {len(df)} != {EXPECTED_TOTAL_HOTSPOTS}"
        )
        # Ensure month label column
        df["month_label"] = df["month"].map(MONTH_LABELS)
        _cache["events"] = df
    return _cache["events"]

def load_hotspot_agg() -> pd.DataFrame:
    """Load aggregated hotspot (by อำเภอ/ตำบล/พ.ศ.)."""
    if "agg" not in _cache:
        df = pd.read_parquet(HOTSPOT_AGG_PATH)
        total = df["hotspot_count"].sum()
        assert total == EXPECTED_TOTAL_HOTSPOTS, (
            f"Aggregated hotspot count mismatch: {total} != {EXPECTED_TOTAL_HOTSPOTS}"
        )
        _cache["agg"] = df
    return _cache["agg"]

def load_joined_table() -> pd.DataFrame:
    """Load OUTER JOIN table (Hotspot × Durian) for Tab 2 & 3."""
    if "joined" not in _cache:
        df = pd.read_parquet(JOINED_TABLE_PATH)
        total = df["hotspot_count"].sum()
        assert total == EXPECTED_TOTAL_HOTSPOTS, (
            f"Joined table hotspot count mismatch: {total} != {EXPECTED_TOTAL_HOTSPOTS}"
        )
        _cache["joined"] = df
    return _cache["joined"]

def get_filter_options(df: pd.DataFrame):
    """Extract unique values for filter dropdowns from events dataframe."""
    amphoe_list = sorted(df["อำเภอ_norm"].dropna().unique().tolist())
    tambon_list = sorted(df["ตำบล_norm"].dropna().unique().tolist())
    pa_types    = sorted(df["ประเภทป่าอนุรักษ์"].dropna().unique().tolist())
    years_be    = sorted(df["พ.ศ."].dropna().unique().tolist())
    return amphoe_list, tambon_list, pa_types, years_be
