# Data Dictionary & Transformation Model

## Source 1: `cleaned_dataset_Wildfire.csv`
*   **Grain:** เหตุการณ์รายจุด (1 แถว = 1 Hotspot)
*   **Transformations required:**
    *   `ว/ด/ป` -> แปลงเป็น Date `date_parsed` (เช่น 2023-11-19)
    *   `พ.ศ.` -> สกัดจาก Date (Year + 543)
    *   `เวลา` (Float) -> สร้างคอลัมน์ `time_hhmm` (String Format `HH:MM`) และ `hour_of_day` (Int)
    *   `อำเภอ_norm`, `ตำบล_norm` -> ลบ Whitespace ทั้งหมดเพื่อใช้เป็น Join Key
    *   `ประเภท_Hotspot_cleaned` -> ค่าที่เป็น 'nominal', 'low', 'high' ให้แปลงเป็น 'ไม่ระบุ'
*   **Aggregation Rule:** Group by `['จังหวัด', 'อำเภอ_norm', 'ตำบล_norm', 'พ.ศ.']` -> `hotspot_count` = count(LAT)

## Source 2: `wildfire_point.csv`
*   **Grain:** ระดับตำบล-ปี (1 แถว = 1 ตำบล/ปี พ.ศ.)
*   **Transformations required:**
    *   `อำเภอ_norm`, `ตำบล_norm` -> ลบ Whitespace 
    *   `จำนวน` -> เปลี่ยนชื่อเป็น `durian_area_rai`

## The Target Data Model (Joined Table for Tab 2 & 3)
*   **Join Type:** **OUTER JOIN** on `['อำเภอ_norm', 'ตำบล_norm', 'พ.ศ.']`
*   **Post-Join Handling:**
    *   ถ้า `hotspot_count` เกิดเป็น `NaN` ให้แทนที่ด้วย `0` (หมายถึงไม่มีไฟป่า)
    *   ถ้า `durian_area_rai` เป็น `NaN` ให้ **คงไว้เป็น NaN** (ห้ามแทนด้วย 0 เพราะหมายถึงไม่มีข้อมูลสำรวจ)