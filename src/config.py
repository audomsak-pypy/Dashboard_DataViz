"""
Executive Configuration, Dark Fire Palette, and Professional Constants.
Kanchanaburi Wildfire and Durian Spatial Analytics (Ultimate Version).
"""

APP_TITLE = "Kanchanaburi Wildfire & Durian Spatial Analytics"
APP_SUBTITLE = "ข้อมูลจุดความร้อนและพื้นที่เพาะปลูกระดับตำบล"

# Data paths
WILDFIRE_DATA_PATH = "data/cleaned_dataset_Wildfire.csv"
DURIAN_DATA_PATH = "data/wildfire_point.csv"

# Data integrity constants
TOTAL_EXPECTED_HOTSPOTS = 8606
LAST_UPDATED_DATE = "2025-08-09"
TOTAL_DETECTION_DAYS = 213
DUPLICATE_COORDS = 0

# Thai Month mapping
THAI_MONTHS = {
    'ม.ค.': 1, 'ก.พ.': 2, 'มี.ค.': 3, 'เม.ย.': 4, 'พ.ค.': 5, 'มิ.ย.': 6,
    'ก.ค.': 7, 'ส.ค.': 8, 'ก.ย.': 9, 'ต.ค.': 10, 'พ.ย.': 11, 'ธ.ค.': 12
}

MONTH_NAMES_TH = {
    1: 'มกราคม', 2: 'กุมภาพันธ์', 3: 'มีนาคม', 4: 'เมษายน',
    5: 'พฤษภาคม', 6: 'มิถุนายน', 7: 'กรกฎาคม', 8: 'สิงหาคม',
    9: 'กันยายน', 10: 'ตุลาคม', 11: 'พฤศจิกายน', 12: 'ธันวาคม'
}

MONTH_NAMES_SHORT_TH = {
    1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.',
    5: 'พ.ค.', 6: 'มิ.ย.', 7: 'ก.ค.', 8: 'ส.ค.',
    9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'
}

# Professional Dark Palette
COLOR_BG_DARK = "#0E1117"
COLOR_CARD_DARK = "#161B22"
COLOR_BORDER_DARK = "#30363D"

# Fire & Heatmap Palette
COLOR_FIRE_PRIMARY = "#E53935"    # Vivid Crimson Red
COLOR_FIRE_ACCENT = "#FF7043"     # Intense Flame Orange
COLOR_FIRE_LIGHT = "#FFA726"      # Golden Amber
COLOR_FIRE_YELLOW = "#FDD835"     # Bright Gold
COLOR_FIRE_DEEP = "#B71C1C"       # Dark Garnet Red

# Durian Emerald Palette
COLOR_DURIAN = "#4ADE80"          # Vivid Mint / Emerald
COLOR_DURIAN_DARK = "#10B981"     # Forest Jade

# Typography & Slate Grays
COLOR_MUTED_GRAY = "#8B949E"      # Subdued text gray
COLOR_TEXT_LIGHT = "#F0F6FC"      # Clean off-white
COLOR_CARD_HOVER = "#1F242C"

# Color sequence for plotly charts
PLOTLY_FIRE_SEQUENCE = ["#E53935", "#FF7043", "#FFA726", "#FDD835", "#AB47BC", "#26A69A", "#42A5F5"]

# Plotly default configuration
PLOTLY_CONFIG = {
    'displayModeBar': False,
    'responsive': True
}

# Disclaimers
CAUSAL_DISCLAIMER_TEXT = (
    "ข้อจำกัดในการตีความ: การเปรียบเทียบใช้ขอบเขตการปกครอง (ตำบล) เป็นเกณฑ์ "
    "ไม่ได้หมายความว่าจุดความร้อนเกิดขึ้นในหรือติดกับแปลงเพาะปลูกทุเรียน "
    "และข้อมูลไม่สามารถสรุปความเป็นเหตุเป็นผลได้"
)

CRS_DISCLAIMER_TEXT = (
    "CRS assumption: Displayed strictly on standard geographic projection. "
    "Spatial distance analysis is disabled."
)

ZERO_MISSING_EXPLANATION = (
    "0.0 ไร่ = สำรวจแล้วไม่พบการเพาะปลูก | "
    "ไม่มีข้อมูล (Null) = ไม่มีข้อมูลการสำรวจในพื้นที่นั้น | "
    "0 จุด = ไม่มีรายงานการตรวจพบจุดความร้อนในเขตปกครองนั้น"
)

BRD_CAUSAL_DISCLAIMER = CAUSAL_DISCLAIMER_TEXT
MAP_CRS_DISCLAIMER = CRS_DISCLAIMER_TEXT
