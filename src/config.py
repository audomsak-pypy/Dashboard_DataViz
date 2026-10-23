"""
Executive Configuration, Dark Fire Palette, and Professional Constants.
"""

APP_TITLE = "Kanchanaburi Wildfire & Durian Spatial Analytics"
APP_SUBTITLE = "ระบบวิเคราะห์ข้อมูลจุดความร้อนในพื้นที่ป่าอนุรักษ์ และพื้นที่เพาะปลูกทุเรียน จังหวัดกาญจนบุรี"

# Data paths
WILDFIRE_DATA_PATH = "data/cleaned_dataset_Wildfire.csv"
DURIAN_DATA_PATH = "data/wildfire_point.csv"

# Data integrity constant
TOTAL_EXPECTED_HOTSPOTS = 8606

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

# Professional Dark Fire Palette
COLOR_BG_DARK = "#0E1117"
COLOR_CARD_DARK = "#161B22"
COLOR_BORDER_DARK = "#30363D"

COLOR_FIRE_PRIMARY = "#E53935"    # Vivid Crimson Red
COLOR_FIRE_ACCENT = "#FF7043"     # Intense Flame Orange
COLOR_FIRE_LIGHT = "#FFA726"      # Golden Amber
COLOR_FIRE_DEEP = "#B71C1C"       # Dark Garnet Red
COLOR_MUTED_GRAY = "#8B949E"      # Subdued text gray
COLOR_TEXT_LIGHT = "#F0F6FC"      # Clean off-white

PLOTLY_FIRE_SEQUENCE = ["#E53935", "#FF7043", "#FFA726", "#FFB74D", "#D32F2F"]

# Plotly default configuration to hide modebar cleanly
PLOTLY_CONFIG = {
    'displayModeBar': False,
    'responsive': True
}

# Disclaimers (Strictly without emojis, concise and academic)
BRD_CAUSAL_DISCLAIMER = (
    "**ข้อกำหนดทางวิชาการและข้อจำกัดของข้อมูล (Academic Disclaimer):** "
    "การเปรียบเทียบใช้ขอบเขตการปกครองระดับตำบลเป็นเกณฑ์ ไม่ได้หมายความว่าจุดความร้อนเกิดขึ้นในหรือติดกับแปลงเพาะปลูกทุเรียน "
    "และข้อมูลไม่สามารถสรุปความเป็นเหตุเป็นผลได้ (No Causal Inference) เนื่องจากไม่มีข้อมูลพิกัดแปลงเพาะปลูกรายแปลง"
)

MAP_CRS_DISCLAIMER = (
    "**หมายเหตุการแสดงผลแผนที่ (CRS Notice):** "
    "แสดงผลบนพิกัดมาตรฐาน Geographic Coordinates (WGS84) ปราศจากการคำนวณระยะห่างเชิงพิกัด"
)

ZERO_MISSING_EXPLANATION = (
    "**คำอธิบายสถานะข้อมูล:** "
    "0.0 ไร่ = สำรวจแล้วไม่พบการเพาะปลูก | "
    "ไม่มีข้อมูล (Null) = ไม่มีข้อมูลการสำรวจในพื้นที่นั้น | "
    "0 จุด = ไม่มีรายงานการตรวจพบจุดความร้อนในเขตปกครองนั้น"
)
