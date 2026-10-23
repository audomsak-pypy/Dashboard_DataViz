"""
Data Loading, Cleaning, Transformation, and Validation Module.
Strict adherence to DATA_DICTIONARY.md and BRD.md.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
from src.config import (
    WILDFIRE_DATA_PATH,
    DURIAN_DATA_PATH,
    TOTAL_EXPECTED_HOTSPOTS,
    THAI_MONTHS,
    MONTH_NAMES_TH
)


def _parse_thai_date(val: str) -> pd.Timestamp:
    """Parses Thai date string such as '19-พ.ย.-23' into a Timestamp."""
    parts = str(val).strip().split('-')
    if len(parts) == 3:
        day = int(parts[0])
        month = THAI_MONTHS.get(parts[1], 1)
        # Year suffix is AD short (e.g., '23' -> 2023)
        year_ad = int(parts[2]) + 2000
        return pd.Timestamp(year=year_ad, month=month, day=day)
    return pd.NaT


def _format_time_float(val) -> tuple[str, int]:
    """
    Parses float time (e.g. 1.17 -> 01:17, 14.2 -> 14:20, 13.05 -> 13:05).
    Returns (time_hhmm, hour_of_day).
    """
    if pd.isna(val):
        return "00:00", 0
    s = f"{float(val):.2f}"
    parts = s.split('.')
    h = int(parts[0])
    m_str = parts[1]
    return f"{h:02d}:{m_str}", h


@st.cache_data
def load_and_process_data():
    """
    Loads raw CSV files, performs cleaning, aggregations, outer joins,
    and validates integrity assertions.
    """
    # 1. Load raw files
    df_wf_raw = pd.read_csv(WILDFIRE_DATA_PATH, encoding='utf-8-sig')
    df_durian_raw = pd.read_csv(DURIAN_DATA_PATH, encoding='utf-8-sig')

    # Validate raw wildfire count
    total_raw_wf = len(df_wf_raw)
    assert total_raw_wf == TOTAL_EXPECTED_HOTSPOTS, (
        f"Expected {TOTAL_EXPECTED_HOTSPOTS} hotspots, got {total_raw_wf}"
    )

    # 2. Process Wildfire Events
    df_wf = df_wf_raw.copy()
    df_wf['date_parsed'] = df_wf['ว/ด/ป'].apply(_parse_thai_date)
    df_wf['พ.ศ.'] = df_wf['date_parsed'].dt.year + 543
    df_wf['month'] = df_wf['date_parsed'].dt.month
    df_wf['month_name'] = df_wf['month'].map(MONTH_NAMES_TH)

    time_tuples = df_wf['เวลา'].apply(_format_time_float)
    df_wf['time_hhmm'] = [t[0] for t in time_tuples]
    df_wf['hour_of_day'] = [t[1] for t in time_tuples]

    # Normalize whitespace for geographic join keys
    df_wf['อำเภอ_norm'] = df_wf['อำเภอ'].astype(str).str.replace(r'\s+', '', regex=True)
    df_wf['ตำบล_norm'] = df_wf['ตำบล'].astype(str).str.replace(r'\s+', '', regex=True)

    # Clean ประเภท Hotspot ('nominal', 'low', 'high' -> 'ไม่ระบุ')
    df_wf['ประเภท_Hotspot_cleaned'] = df_wf['ประเภท Hotspot'].replace({
        'nominal': 'ไม่ระบุ',
        'low': 'ไม่ระบุ',
        'high': 'ไม่ระบุ'
    })

    # Standardize CONFEDENCE display
    df_wf['CONFEDENCE'] = df_wf['CONFEDENCE'].fillna('ไม่ระบุ')

    # 3. Aggregate Wildfire by Tambon & Year
    wf_agg = df_wf.groupby(
        ['จังหวัด', 'อำเภอ_norm', 'ตำบล_norm', 'พ.ศ.'],
        as_index=False
    ).agg(
        hotspot_count=('LAT', 'count')
    )

    # Verify agg count
    assert wf_agg['hotspot_count'].sum() == TOTAL_EXPECTED_HOTSPOTS, (
        f"Aggregated count {wf_agg['hotspot_count'].sum()} != {TOTAL_EXPECTED_HOTSPOTS}"
    )

    # 4. Process Durian Data
    df_durian = df_durian_raw.copy()
    df_durian['อำเภอ_norm'] = df_durian['อำเภอ'].astype(str).str.replace(r'\s+', '', regex=True)
    df_durian['ตำบล_norm'] = df_durian['ตำบล'].astype(str).str.replace(r'\s+', '', regex=True)
    df_durian = df_durian.rename(columns={'จำนวน': 'durian_area_rai'})

    # 5. Outer Join according to DATA_DICTIONARY.md
    joined = pd.merge(
        df_durian,
        wf_agg,
        on=['อำเภอ_norm', 'ตำบล_norm', 'พ.ศ.'],
        how='outer',
        suffixes=('_durian', '_wf')
    )

    # If hotspot_count is NaN, replace with 0 (no wildfire in that administrative unit)
    joined['hotspot_count'] = joined['hotspot_count'].fillna(0).astype(int)

    # Note: If durian_area_rai is NaN, keep it as NaN (no survey conducted, NOT zero)
    # Validate post-join hotspot count sum
    total_joined_wf = joined['hotspot_count'].sum()
    assert total_joined_wf == TOTAL_EXPECTED_HOTSPOTS, (
        f"Joined hotspot count {total_joined_wf} != {TOTAL_EXPECTED_HOTSPOTS}"
    )

    # Add helper column for status
    def _get_survey_status(row):
        if pd.isna(row['durian_area_rai']):
            return 'ไม่มีข้อมูลการสำรวจ (Null)'
        elif row['durian_area_rai'] == 0:
            return 'สำรวจแล้วไม่มีการปลูก (0.0 ไร่)'
        else:
            return 'มีการเพาะปลูกทุเรียน'

    joined['durian_status'] = joined.apply(_get_survey_status, axis=1)

    return {
        'events': df_wf,          # 8,606 individual hotspot points with coordinates & times
        'durian_raw': df_durian,  # Durian historical survey data 2561-2568
        'joined': joined,         # Outer joined tambon-year data model
        'total_hotspots': TOTAL_EXPECTED_HOTSPOTS
    }
