# 🔥 Kanchanaburi Wildfire & Durian Cultivation Observatory
> **ระบบสำรวจและเปรียบเทียบข้อมูลจุดความร้อนในพื้นที่ป่าอนุรักษ์ กับข้อมูลพื้นที่เพาะปลูกทุเรียน จังหวัดกาญจนบุรี**

Dashboard นี้ได้รับการออกแบบและยกระดับ UI/UX โดยอิงตามแนวทางการจัดวางสไตล์ **Global Forest Fire Dashboard (Cockpit Observatory Layout)** พร้อมระบบ **Two-Way Global Cross-Filtering** ที่เชื่อมโยงกราฟ แผนที่ และตารางข้อมูลเข้าด้วยกันทั้งหมด 100%

---

## 🎨 การออกแบบและการเชื่อมโยงข้อมูล (Interconnected Analytics)

### 1. Header & Quick Indicators (สไตล์ SAS Viya Cockpit)
- **Top Navigation Banner**: โลโก้ Global Observatory พร้อมยอดรวมจุดความร้อนรวม `8,606 จุด`, ยอดพื้นที่ปลูกทุเรียนล่าสุด `8,129 ไร่`
- **Active Filter Pills Bar**: แสดงแถบป้ายสถานะตัวกรองที่กำลังใช้งาน (เช่น ตำบล, อำเภอ, ระดับความเชื่อมั่น, ประเภทป่า) พร้อมปุ่ม Reset All

### 2. แผงควบคุมและกราฟวิเคราะห์ (Left Analytics Panel)
- **Semi-Circular Gauges**:
  - `Active Hotspot Intensity`: มาตรวัดระดับความรุนแรงของจุดความร้อนตามพื้นที่ที่เลือก (เทียบสเกล 3 ระดับ เขียว/ส้ม/แดง)
  - `Durian Cultivation Area`: มาตรวัดพื้นที่ปลูกทุเรียนตามพื้นที่ที่เลือก
- **Most Active Hours List**: แสดงช่วงเวลาเกิดเหตุสูงสุด 5 อันดับแรก (พร้อมป้ายระบุจำนวนจุดสไตล์ SAS Viya)
- **Monthly Fire Activity**: กราฟผสม Bar + Spline Area Chart แสดงวงจรฤดูกาลเกิดไฟป่า (*คลิกที่แท่งเพื่อกรองเดือน*)
- **Confidence Donut Ring**: วงแหวนหนาแสดงระดับความน่าเชื่อถือ พร้อมตัวเลขยอดรวมตรงกลาง (*คลิกที่ชิ้นเพื่อกรอง CONFEDENCE*)
- **Forest Cover Treemap**: บล็อกโมเสกสัดส่วนประเภทป่าอนุรักษ์ (*คลิกที่บล็อกเพื่อกรองประเภทป่า*)
- **Simple Comparison**: กราฟแท่งเปรียบเทียบค่าเฉลี่ยจุดความร้อนระหว่างกลุ่มตำบลปลูกทุเรียน vs ไม่ปลูก
- **Dynamic Context Card**: กล่องข้อความสัญลักษณ์ `?` อธิบายบริบทเชิงพื้นที่และตอกย้ำข้อจำกัด Causal Disclaimer

### 3. แผนที่ดาวเทียมและตารางข้อมูลเชิงลึก (Right Interactive Panel)
- **Satellite / Dark Matter Map**: แผนที่ดาวเทียมความละเอียดสูง แสดงพิกัดจุดความร้อน พร้อมปุ่มสลับโหมดดาวเทียม/ดาร์กแมตเตอร์ (*คลิกที่จุดบนแผนที่เพื่อกรองตำบล*)
- **Durian Cultivation DataTable**: ตารางอันดับพื้นที่ปลูกทุเรียนรายตำบล พร้อมไฮไลท์ข้อมูลศูนย์ (`🟡 0.0 ไร่`) และ Missing (`⬜ Missing`) (*คลิกเลือกแถวเพื่อกรองทั้งหน้าจอ*)
- **Annual Trend Line**: กราฟเส้นแสดงแนวโน้มพื้นที่ปลูกทุเรียนย้อนหลัง พ.ศ. 2561–2568 สำหรับพื้นที่ที่เลือก

---

## 🛠️ โครงสร้างไฟล์ในโครงการ

```
d:\Dashboard_DataViz\
├── app.py                     # แอปพลิเคชันหลัก (Single-Page Dash Layout & Callbacks)
├── config.py                  # ค่าคงที่, Paths, สีธีม, ข้อความ Disclaimer
├── data_prep.py               # สคริปต์ทำความสะอาดและแปลงโมเดลข้อมูล (Phase 2)
├── profiling.py               # สคริปต์ตรวจสอบคุณภาพข้อมูลเบื้องต้น (Phase 1)
├── profiling_log.txt          # รายงาน Data Profiling
├── requirements.txt           # รายการ Libraries ที่จำเป็น
├── README.md                  # เอกสารแนะนำการติดตั้งและใช้งาน
├── .gitignore
├── data/
│   ├── cleaned_dataset_Wildfire.csv   # ข้อมูลดิบจุดความร้อน (8,606 แถว)
│   ├── wildfire_point.csv             # ข้อมูลดิบพื้นที่ปลูกทุเรียน (441 แถว)
│   ├── hotspot_events.parquet         # ข้อมูลจุดความร้อนที่ผ่านการ Cleaned & Transformed
│   ├── hotspot_agg.parquet            # ข้อมูลจุดความร้อน Aggregated รายตำบล/ปี
│   └── joined_table.parquet           # ข้อมูล OUTER JOIN ระหว่าง Hotspot และทุเรียน
└── utils/
    ├── __init__.py
    └── data_loader.py         # ฟังก์ชันโหลดข้อมูลพร้อม Assertion ตรวจสอบความถูกต้อง
```

---

## 🚀 วิธีการติดตั้งและเริ่มใช้งาน

### 1. ติดตั้ง Virtual Environment และ Dependencies
```powershell
# สร้าง venv (หากยังไม่มี)
python -m venv .venv

# ติดตั้งแพ็กเกจ
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. เตรียมข้อมูล (หากต้องการ Re-generate ข้อมูล Parquet)
```powershell
.\.venv\Scripts\python data_prep.py
```
*ระบบจะตรวจสอบ Assertion `sum(hotspot_count) == 8,606` ทั้งก่อนและหลัง JOIN*

### 3. รันแดชบอร์ด
```powershell
.\.venv\Scripts\python app.py
```
เปิดเบราว์เซอร์ไปที่: **`http://127.0.0.1:8050/`**

---

## 🔍 การทดสอบระบบ Cross-Filtering
1. **การคลิกจุดบนแผนที่**: เมื่อคลิกจุดความร้อนบนแผนที่ แดชบอร์ดจะกรองตารางทุเรียน, กราฟแนวโน้ม, กราฟรายเดือน และส่วนเปรียบเทียบ ให้แสดงผลเฉพาะตำบลนั้นทันที
2. **การคลิกแถวในตารางทุเรียน**: เมื่อคลิกเลือกแถวตำบลใดตำบลหนึ่ง แผนที่จะ Zoom/Focus และกรองจุดความร้อนเฉพาะตำบลดังกล่าว
3. **การล้างตัวกรอง**: กดปุ่ม **"ล้างพื้นที่เลือก"** ที่แผงตัวกรองด้านบนเพื่อกลับสู่การแสดงผลภาพรวมทั้งจังหวัด
