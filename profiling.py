"""
Phase 1: Data Profiling & Validation Script
ตาม HanDoff.md Phase 1
Output: profiling_log.txt
"""
import sys
import io
import pandas as pd
import numpy as np

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

LOG_LINES = []

def log(msg=""):
    print(msg)
    LOG_LINES.append(msg)

def sep(title=""):
    line = "=" * 60
    log(line)
    if title:
        log(f"  {title}")
        log(line)

# ─── Load Data ───────────────────────────────────────────────
df_hotspot = pd.read_csv("data/cleaned_dataset_Wildfire.csv", encoding="utf-8-sig")
df_durian  = pd.read_csv("data/wildfire_point.csv",           encoding="utf-8-sig")

# ─── SOURCE 1: cleaned_dataset_Wildfire.csv ──────────────────
sep("SOURCE 1: cleaned_dataset_Wildfire.csv")
log(f"Shape            : {df_hotspot.shape}")
log(f"Total Hotspots   : {len(df_hotspot)}  (Expected: 8,606 → {'✓ OK' if len(df_hotspot)==8606 else '✗ MISMATCH'})")
log()

log("--- Column dtypes ---")
for col in df_hotspot.columns:
    log(f"  {col:<30} {str(df_hotspot[col].dtype):<12}  nulls={df_hotspot[col].isna().sum()}")

log()
log("--- Key column value ranges ---")
log(f"  LAT   : min={df_hotspot['LAT'].min():.5f}  max={df_hotspot['LAT'].max():.5f}")
log(f"  LONG  : min={df_hotspot['LONG'].min():.5f}  max={df_hotspot['LONG'].max():.5f}")
log(f"  เวลา  : min={df_hotspot['เวลา'].min()}  max={df_hotspot['เวลา'].max()}  nulls={df_hotspot['เวลา'].isna().sum()}")

log()
log("--- ว/ด/ป sample values ---")
log(f"  Unique date count  : {df_hotspot['ว/ด/ป'].nunique()}")
log(f"  Sample dates       : {df_hotspot['ว/ด/ป'].dropna().head(5).tolist()}")

log()
log("--- จังหวัด unique values ---")
log(f"  {df_hotspot['จังหวัด'].unique().tolist()}")

log()
log("--- อำเภอ: whitespace check ---")
has_ws_amphoe = df_hotspot['อำเภอ'].apply(lambda x: str(x) != str(x).strip() if pd.notna(x) else False).sum()
log(f"  อำเภอ rows with leading/trailing whitespace : {has_ws_amphoe}")
has_ws_tambon = df_hotspot['ตำบล'].apply(lambda x: str(x) != str(x).strip() if pd.notna(x) else False).sum()
log(f"  ตำบล  rows with leading/trailing whitespace : {has_ws_tambon}")

log()
log("--- CONFEDENCE distribution ---")
log(df_hotspot['CONFEDENCE'].value_counts().to_string())

log()
log("--- ประเภท Hotspot distribution ---")
log(df_hotspot['ประเภท Hotspot'].value_counts().to_string())

log()
log("--- ประเภทป่าอนุรักษ์ distribution ---")
log(df_hotspot['ประเภทป่าอนุรักษ์'].value_counts().to_string())

log()
log("--- สถานีฯที่รับผิดชอบ distribution ---")
log(df_hotspot['สถานีฯที่รับผิดชอบ'].value_counts().to_string())

log()
log("--- Year distribution (from ว/ด/ป) ---")
# Try to extract year from ว/ด/ป  e.g. "19-พ.ย.-23"
def extract_year_th(s):
    if pd.isna(s):
        return None
    parts = str(s).split('-')
    if len(parts) >= 3:
        try:
            yr_short = int(parts[-1])
            # Assume 2-digit: 23 = 2566 BE  (CE+543 -> BE; CE23=2023 BE=2566)
            # The data uses CE year (23=2023)
            return yr_short + 2000
        except:
            return None
    return None

df_hotspot['_year_CE'] = df_hotspot['ว/ด/ป'].apply(extract_year_th)
log(df_hotspot['_year_CE'].value_counts().sort_index().to_string())

log()
log("--- อำเภอ unique values ---")
log(f"  Unique อำเภอ count: {df_hotspot['อำเภอ'].nunique()}")
log(f"  Values: {sorted(df_hotspot['อำเภอ'].dropna().unique().tolist())}")

log()
log("--- ตำบล unique values ---")
log(f"  Unique ตำบล count: {df_hotspot['ตำบล'].nunique()}")

# ─── SOURCE 2: wildfire_point.csv ────────────────────────────
sep("SOURCE 2: wildfire_point.csv (Durian)")
log(f"Shape            : {df_durian.shape}")
log()

log("--- Column dtypes ---")
for col in df_durian.columns:
    log(f"  {col:<20} {str(df_durian[col].dtype):<12}  nulls={df_durian[col].isna().sum()}")

log()
log("--- พ.ศ. unique values ---")
log(f"  {sorted(df_durian['พ.ศ.'].unique().tolist())}")

log()
log("--- จำนวน (durian area rai) stats ---")
log(f"  min    : {df_durian['จำนวน'].min()}")
log(f"  max    : {df_durian['จำนวน'].max()}")
log(f"  mean   : {df_durian['จำนวน'].mean():.2f}")
log(f"  nulls  : {df_durian['จำนวน'].isna().sum()}")
log(f"  zeros  : {(df_durian['จำนวน'] == 0).sum()}")

log()
log("--- อำเภอ whitespace check (durian) ---")
has_ws_amp_d = df_durian['อำเภอ'].apply(lambda x: str(x) != str(x).strip() if pd.notna(x) else False).sum()
log(f"  Rows with whitespace in อำเภอ: {has_ws_amp_d}")
has_ws_tab_d = df_durian['ตำบล'].apply(lambda x: str(x) != str(x).strip() if pd.notna(x) else False).sum()
log(f"  Rows with whitespace in ตำบล : {has_ws_tab_d}")

log()
log("--- อำเภอ unique values (durian) ---")
log(f"  Unique อำเภอ: {sorted(df_durian['อำเภอ'].dropna().unique().tolist())}")

log()
log("--- ตำบล unique values count (durian) ---")
log(f"  Unique ตำบล: {df_durian['ตำบล'].nunique()}")

# ─── JOIN KEY OVERLAP CHECK ───────────────────────────────────
sep("JOIN KEY OVERLAP (อำเภอ_norm x ตำบล_norm)")
df_h = df_hotspot.copy()
df_h['อำเภอ_norm'] = df_h['อำเภอ'].str.strip()
df_h['ตำบล_norm']  = df_h['ตำบล'].str.strip()

df_d = df_durian.copy()
df_d['อำเภอ_norm'] = df_d['อำเภอ'].str.strip()
df_d['ตำบล_norm']  = df_d['ตำบล'].str.strip()

keys_h = set(zip(df_h['อำเภอ_norm'], df_h['ตำบล_norm']))
keys_d = set(zip(df_d['อำเภอ_norm'], df_d['ตำบล_norm']))

overlap = keys_h & keys_d
only_h  = keys_h - keys_d
only_d  = keys_d - keys_h

log(f"  Unique (อำเภอ, ตำบล) pairs in Hotspot data : {len(keys_h)}")
log(f"  Unique (อำเภอ, ตำบล) pairs in Durian data  : {len(keys_d)}")
log(f"  Overlapping pairs                           : {len(overlap)}")
log(f"  Only in Hotspot (no durian record)          : {len(only_h)}")
log(f"  Only in Durian  (no hotspot record)         : {len(only_d)}")

log()
log("--- Sample pairs only in Hotspot ---")
for p in sorted(list(only_h))[:10]:
    log(f"  {p}")

log()
log("--- Sample pairs only in Durian ---")
for p in sorted(list(only_d))[:10]:
    log(f"  {p}")

sep("END OF PROFILING REPORT")

# ─── Write profiling_log.txt ──────────────────────────────────
with open("profiling_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(LOG_LINES))

print("\n✓ profiling_log.txt written successfully.")
