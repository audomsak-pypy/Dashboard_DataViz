"""
Configuration, Constants, Styling, and Disclaimers for the Dashboard.
"""

APP_TITLE = "Kanchanaburi Wildfire & Durian Insights"
APP_SUBTITLE = "ระบบวิเคราะห์ข้อมูลจุดความร้อนในป่าอนุรักษ์ และพื้นที่เพาะปลูกทุเรียน จ.กาญจนบุรี"

# File paths
WILDFIRE_DATA_PATH = "data/cleaned_dataset_Wildfire.csv"
DURIAN_DATA_PATH = "data/wildfire_point.csv"

# Expected constants
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

# Color palette inspired by modern geospatial & forestry analytics
COLOR_FIRE_ORANGE = "#FF5722"
COLOR_FIRE_RED = "#D32F2F"
COLOR_DURIAN_GREEN = "#2E7D32"
COLOR_DURIAN_YELLOW = "#FBC02D"
COLOR_FOREST_DARK = "#1B5E20"
COLOR_ACCENT_BLUE = "#0288D1"
COLOR_CARD_BG = "#F8F9FA"

# Disclaimers required by BRD and HanDoff
BRD_CAUSAL_DISCLAIMER = (
    "⚠️ **ข้อกำหนดทางวิชาการและข้อจำกัดของข้อมูล (Academic Disclaimer):**\n\n"
    "การเปรียบเทียบใช้ขอบเขตการปกครอง (ตำบล) เป็นเกณฑ์ "
    "ไม่ได้หมายความว่าจุดความร้อนเกิดขึ้นในหรือติดกับแปลงเพาะปลูกทุเรียน "
    "และข้อมูลไม่สามารถสรุปความเป็นเหตุเป็นผลได้ (No Causal Inference) "
    "เนื่องจากไม่มีข้อมูลพิกัดแปลงเพาะปลูกรายแปลง และไม่มีข้อมูล Polygon ขอบเขตตำบล"
)

MAP_CRS_DISCLAIMER = (
    "📌 **หมายเหตุการแสดงผลแผนที่ (CRS Notice):** "
    "แสดงผลบนพิกัดมาตรฐาน Geographic Coordinates (WGS84) "
    "ไม่มีการคำนวณระยะห่างเชิงพิกัดจากแปลงเพาะปลูกเนื่องจากไม่มีพิกัดแปลงปลูก"
)

ZERO_MISSING_EXPLANATION = (
    "💡 **คำอธิบายสัญลักษณ์ข้อมูล:**\n"
    "- `Durian = 0.0 ไร่`: สำรวจแล้ว มีรายงานว่าไม่มีการปลูก\n"
    "- `Durian = ไม่มีข้อมูล (Null)`: พื้นที่ที่ไม่มีรายงานการสำรวจ\n"
    "- `Hotspot = 0 จุด`: ไม่มีรายงานการตรวจพบจุดความร้อนในเขตปกครองนั้นในรอบปีที่ระบุ"
)
