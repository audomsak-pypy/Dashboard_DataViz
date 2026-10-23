# config.py — Central configuration for the Dashboard
import os

# ─── Paths ────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")

HOTSPOT_EVENTS_PATH = os.path.join(DATA_DIR, "hotspot_events.parquet")
HOTSPOT_AGG_PATH    = os.path.join(DATA_DIR, "hotspot_agg.parquet")
JOINED_TABLE_PATH   = os.path.join(DATA_DIR, "joined_table.parquet")

# ─── App Meta ─────────────────────────────────────────────────
APP_TITLE = "Kanchanaburi Wildfire & Durian Dashboard"

# ─── BRD Constants ────────────────────────────────────────────
EXPECTED_TOTAL_HOTSPOTS = 8606

# ─── Disclaimer (BRD Section 5) ───────────────────────────────
CAUSAL_DISCLAIMER = (
    "การเปรียบเทียบใช้ขอบเขตการปกครอง (ตำบล) เป็นเกณฑ์ "
    "ไม่ได้หมายความว่าจุดความร้อนเกิดขึ้นในหรือติดกับแปลงเพาะปลูกทุเรียน "
    "และข้อมูลไม่สามารถสรุปความเป็นเหตุเป็นผลได้"
)

MAP_CRS_NOTE = (
    "CRS assumption: Displayed strictly on standard geographic projection. "
    "Spatial distance analysis is disabled."
)

# ─── Thai Month Labels ────────────────────────────────────────
MONTH_LABELS = {
    1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.",
    5: "พ.ค.", 6: "มิ.ย.", 7: "ก.ค.", 8: "ส.ค.",
    9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค.",
}

# ─── Color Palette ────────────────────────────────────────────
COLORS = {
    "primary":     "#E85D04",   # fire orange
    "secondary":   "#F48C06",   # amber
    "durian":      "#70A500",   # durian green
    "background":  "#1A1A2E",   # dark navy
    "card":        "#16213E",   # card dark
    "card_border": "#0F3460",   # border blue
    "text":        "#E0E0E0",   # light text
    "muted":       "#A0A0B0",   # muted text
    "warning":     "#FFB703",   # yellow warning
    "low":         "#8ecae6",
    "high":        "#e63946",
}
