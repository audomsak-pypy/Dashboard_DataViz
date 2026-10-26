"""
Phase 2: Data Model Preparation
ตาม HanDoff.md Phase 2 + Data_Dictionary.md + HANDOFF_Dashboard_Pre_Presentation_Fixes.md

Actions:
1. Parse Dates and Time (convert Float to HH:MM)
2. Filter out non-wildfire records (การจัดการเชื้อเพลิง, เข้าตรวจสอบแล้วไม่พบไฟ, ดำเนินคดี)
3. Clean ประเภท Hotspot (nominal, low, high -> ไม่ระบุ)
4. Normalize geographic strings
5. Aggregate cleaned_dataset_Wildfire.csv by [อำเภอ_norm, ตำบล_norm, พ.ศ.] BEFORE joining
6. Perform OUTER JOIN with wildfire_point.csv
7. Apply Zero/NaN logic according to DATA_DICTIONARY.md

Test: Assert sum(hotspot_count) == 7865
Output: processed data saved to data/
"""
import sys
import io
import re
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ─── Constants ────────────────────────────────────────────────
EXPECTED_TOTAL_HOTSPOTS = 7865

THAI_MONTH_MAP = {
    "ม.ค.":  1, "ก.พ.":  2, "มี.ค.":  3, "เม.ย.":  4,
    "พ.ค.":  5, "มิ.ย.":  6, "ก.ค.":  7, "ส.ค.":  8,
    "ก.ย.":  9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12,
}

HOTSPOT_TYPE_REMAP = {"nominal": "ไม่ระบุ", "low": "ไม่ระบุ", "high": "ไม่ระบุ"}

# ─── Helper: Parse Thai date string ──────────────────────────
def parse_thai_date(s):
    """
    Parse date string like '19-พ.ย.-23' into a proper date.
    Year is 2-digit CE (23 → 2023).
    Returns pd.Timestamp or NaT.
    """
    if pd.isna(s):
        return pd.NaT
    s = str(s).strip()
    parts = s.split("-")
    if len(parts) != 3:
        return pd.NaT
    try:
        day   = int(parts[0])
        month = THAI_MONTH_MAP.get(parts[1], None)
        yr_short = int(parts[2])
        year  = yr_short + 2000  # 23 → 2023 (CE)
        if month is None:
            return pd.NaT
        return pd.Timestamp(year=year, month=month, day=day)
    except Exception:
        return pd.NaT

# ─── Helper: Parse เวลา float → HH:MM ────────────────────────
def parse_time_float(val):
    """
    Convert float like 1.17 → '01:17', 14.39 → '14:39'.
    The integer part = hour, decimal part = minutes (2 digits).
    """
    if pd.isna(val):
        return None, None
    val_str = f"{val:.2f}"
    parts   = val_str.split(".")
    hour    = int(parts[0])
    minute  = int(parts[1]) if len(parts) > 1 else 0
    hhmm    = f"{hour:02d}:{minute:02d}"
    return hhmm, hour

# ─── STEP 1: Load raw data ─────────────────────────────────────
print("=" * 60)
print("STEP 1: Loading raw CSVs")
print("=" * 60)

df_hotspot_raw = pd.read_csv("data/cleaned_dataset_Wildfire.csv", encoding="utf-8-sig")
df_durian_raw  = pd.read_csv("data/wildfire_point.csv",           encoding="utf-8-sig")

print(f"  Hotspot raw shape : {df_hotspot_raw.shape}")
print(f"  Durian  raw shape : {df_durian_raw.shape}")

# ─── STEP 2: Transform cleaned_dataset_Wildfire.csv ──────────
print()
print("=" * 60)
print("STEP 2: Transforming Hotspot data & Data Cleaning")
print("=" * 60)

df_h = df_hotspot_raw.copy()

# 2a. Filter out non-wildfire records per HANDOFF_Dashboard_Pre_Presentation_Fixes.md
exclude_mask = df_h["หมายเหตุ"].astype(str).str.contains(
    "การจัดการเชื้อเพลิง|เข้าตรวจสอบแล้วไม่พบไฟ|ดำเนินคดี", na=False
)
print(f"  Excluding non-wildfire rows from หมายเหตุ : {exclude_mask.sum()} rows")
df_h = df_h[~exclude_mask].copy()
print(f"  Cleaned Hotspot records                   : {len(df_h)} rows")

# 2b. Parse date
df_h["date_parsed"] = df_h["ว/ด/ป"].apply(parse_thai_date)
parse_fail = df_h["date_parsed"].isna().sum()
print(f"  Date parse failures : {parse_fail} (expected 0)")

# 2c. Derive พ.ศ. (Buddhist Era = CE + 543)
df_h["พ.ศ."] = df_h["date_parsed"].dt.year + 543

# 2d. Parse เวลา float → HH:MM + hour_of_day
df_h[["time_hhmm", "hour_of_day"]] = df_h["เวลา"].apply(
    lambda v: pd.Series(parse_time_float(v))
)
print(f"  time_hhmm sample  : {df_h['time_hhmm'].head(5).tolist()}")
print(f"  hour_of_day range : {df_h['hour_of_day'].min()} – {df_h['hour_of_day'].max()}")

# 2e. Normalize geographic strings (strip whitespace → join keys)
df_h["อำเภอ_norm"] = df_h["อำเภอ"].str.strip()
df_h["ตำบล_norm"]  = df_h["ตำบล"].str.strip()

# 2f. Clean ประเภท Hotspot (remap nominal, low, high to ไม่ระบุ)
df_h["ประเภท Hotspot"] = df_h["ประเภท Hotspot"].replace(HOTSPOT_TYPE_REMAP)
df_h["ประเภท_Hotspot_cleaned"] = df_h["ประเภท Hotspot"]
print(f"  ประเภท_Hotspot_cleaned value counts:")
for k, v in df_h["ประเภท_Hotspot_cleaned"].value_counts().items():
    print(f"    {k}: {v}")

# 2g. Month column for temporal analysis
df_h["month"] = df_h["date_parsed"].dt.month

print(f"  Hotspot df shape after transforms: {df_h.shape}")

# ─── STEP 3: Aggregate Hotspot BEFORE join ────────────────────
print()
print("=" * 60)
print("STEP 3: Aggregating Hotspot by [จังหวัด, อำเภอ_norm, ตำบล_norm, พ.ศ.]")
print("=" * 60)

df_hotspot_agg = (
    df_h.groupby(["จังหวัด", "อำเภอ_norm", "ตำบล_norm", "พ.ศ."], as_index=False)
    .agg(hotspot_count=("LAT", "count"))
)

total_agg = df_hotspot_agg["hotspot_count"].sum()
print(f"  Aggregated shape     : {df_hotspot_agg.shape}")
print(f"  Sum of hotspot_count : {total_agg}  (Expected: {EXPECTED_TOTAL_HOTSPOTS})")

# ─── ASSERTION ────────────────────────────────────────────────
assert total_agg == EXPECTED_TOTAL_HOTSPOTS, (
    f"✗ ASSERTION FAILED: sum(hotspot_count) = {total_agg}, expected {EXPECTED_TOTAL_HOTSPOTS}"
)
print(f"  ✓ ASSERTION PASSED: sum(hotspot_count) == {EXPECTED_TOTAL_HOTSPOTS}")

# ─── STEP 4: Transform Durian data ───────────────────────────
print()
print("=" * 60)
print("STEP 4: Transforming Durian data")
print("=" * 60)

df_d = df_durian_raw.copy()
df_d["อำเภอ_norm"]       = df_d["อำเภอ"].str.strip()
df_d["ตำบล_norm"]        = df_d["ตำบล"].str.strip()
df_d["durian_area_rai"]  = df_d["จำนวน"]   # rename as per Data Dictionary

print(f"  Durian df shape    : {df_d.shape}")
print(f"  พ.ศ. range         : {df_d['พ.ศ.'].min()} – {df_d['พ.ศ.'].max()}")
print(f"  durian_area_rai nulls : {df_d['durian_area_rai'].isna().sum()}")
print(f"  durian_area_rai zeros : {(df_d['durian_area_rai'] == 0).sum()}")

# ─── STEP 5: OUTER JOIN ───────────────────────────────────────
print()
print("=" * 60)
print("STEP 5: OUTER JOIN on [อำเภอ_norm, ตำบล_norm, พ.ศ.]")
print("=" * 60)

df_d_for_join = df_d[["จังหวัด", "อำเภอ_norm", "ตำบล_norm", "พ.ศ.", "durian_area_rai"]].copy()

df_joined = pd.merge(
    df_hotspot_agg,
    df_d_for_join,
    on=["อำเภอ_norm", "ตำบล_norm", "พ.ศ."],
    how="outer",
    suffixes=("_hotspot", "_durian"),
)

if "จังหวัด_hotspot" in df_joined.columns:
    df_joined["จังหวัด"] = df_joined["จังหวัด_hotspot"].fillna(df_joined["จังหวัด_durian"])
    df_joined.drop(columns=["จังหวัด_hotspot", "จังหวัด_durian"], inplace=True)

print(f"  Joined shape: {df_joined.shape}")
print(f"  hotspot_count nulls (before fill): {df_joined['hotspot_count'].isna().sum()}")
print(f"  durian_area_rai nulls (before fill): {df_joined['durian_area_rai'].isna().sum()}")

# ─── STEP 6: Apply Zero/NaN logic ─────────────────────────────
print()
print("=" * 60)
print("STEP 6: Applying Zero/NaN logic (per Data Dictionary)")
print("=" * 60)

df_joined["hotspot_count"] = df_joined["hotspot_count"].fillna(0).astype(int)

print(f"  hotspot_count nulls (after fill)    : {df_joined['hotspot_count'].isna().sum()}")
print(f"  durian_area_rai nulls (after fill)  : {df_joined['durian_area_rai'].isna().sum()}")

# ─── FINAL ASSERTION ──────────────────────────────────────────
total_joined = df_joined["hotspot_count"].sum()
print()
print(f"  Final sum(hotspot_count) = {total_joined}  (Expected: {EXPECTED_TOTAL_HOTSPOTS})")
assert total_joined == EXPECTED_TOTAL_HOTSPOTS, (
    f"✗ POST-JOIN ASSERTION FAILED: sum = {total_joined}"
)
print(f"  ✓ POST-JOIN ASSERTION PASSED")

# ─── SAVE OUTPUTS ─────────────────────────────────────────────
print()
print("=" * 60)
print("SAVING PROCESSED DATA")
print("=" * 60)

df_h.to_parquet("data/hotspot_events.parquet", index=False)
print("  ✓ data/hotspot_events.parquet  (event-level, all transforms)")

df_hotspot_agg.to_parquet("data/hotspot_agg.parquet", index=False)
print("  ✓ data/hotspot_agg.parquet     (aggregated by อำเภอ/ตำบล/พ.ศ.)")

df_joined.to_parquet("data/joined_table.parquet", index=False)
print("  ✓ data/joined_table.parquet    (OUTER JOIN result for Tab 2 & 3)")

print()
print("=" * 60)
print("  Data Preparation COMPLETE ✓")
print("=" * 60)
