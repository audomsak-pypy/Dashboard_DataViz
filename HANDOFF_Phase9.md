# HANDOFF_Phase9.md: Advanced Analytics & UI Refactoring

## 1. บริบทและเป้าหมาย (Context & Objective)
ต่อยอดจาก Dashboard เดิม (Phase 8) เราต้องการเพิ่มโมดูลการวิเคราะห์เชิงลึก (Seasonality, Risk, Correlation, Data Quality) และ **รื้อถอนกราฟ Gauge เดิม** ที่กินพื้นที่ เพื่อเปลี่ยนเป็นรูปแบบที่เข้าใจง่ายกว่า โดย **ทุกกราฟต้องอยู่ในหน้าเดียว (Single-Page)** และเชื่อมต่อกันด้วย **Global Cross-Filtering** ทั้งหมด

---

## 2. ขอบเขตงาน (Sub-phases)
ให้ AI (Codex/Antigravity) ทำงานเรียงตามลำดับ Phase ห้ามทำข้าม และตรวจสอบโค้ดให้รันผ่านก่อนส่งมอบ

### Phase 9A — UI Refactoring: เปลี่ยนกราฟ Gauge และปรับ Layout
**เป้าหมาย:** เพิ่มพื้นที่แสดงผลโดยเปลี่ยน Gauge เป็น KPI Cards ที่กระชับและสื่อสารได้ดีกว่า
1. **ลบกราฟ Gauge ทั้งสองตัวทิ้ง:** ลบ `ACTIVE HOTSPOT INTENSITY` และ `DURIAN CULTIVATION AREA` 
2. **สร้าง KPI Scorecards แทนที่:** ใช้ Card layout แสดงตัวเลขขนาดใหญ่ (Big Numbers) ดังนี้:
   - **Card 1: Total Hotspots** (จุดความร้อนสะสมตาม Filter) พร้อมตัวเลข Delta เทียบปีก่อนหน้า (YoY)
   - **Card 2: Durian Area** (พื้นที่ปลูกทุเรียนรวมในพื้นที่และปีที่เลือก) หน่วยเป็น 'ไร่'
   - **Card 3: Data Quality Score** (สัดส่วน Hotspot ระดับ High/Nominal Confidence เป็นเปอร์เซ็นต์)
3. **จัด Layout ใหม่:** วาง KPI Cards ไว้แถวบนสุด (Top Row) ใต้ Global Filters เพื่อให้เหลือพื้นที่ด้านล่างสำหรับกราฟใหม่

### Phase 9B — โมดูล Seasonality & Trend (ฤดูกาลและแนวโน้ม)
**เป้าหมาย:** วิเคราะห์ช่วงเวลาเกิดไฟป่า
1. **สร้างกราฟ Line/Bar Combo (รายเดือน):** แกน X เป็นเดือน แกน Y เป็นจำนวน Hotspot โดยให้มีเส้นเปรียบเทียบระหว่างปี (เช่น เส้นปี 66, 67, 68 ซ้อนกัน)
2. **เพิ่มตัวแบ่งฤดูกาล (Seasonality Indicator):** สร้างตัวแปรฤดูกาล (ฤดูแล้ง = พ.ย.-เม.ย., ฤดูฝน = พ.ค.-ต.ค.) และแสดง Stacked Bar หรือ Pie chart เปรียบเทียบสัดส่วน Hotspot ระหว่างฤดูแล้ง vs ฤดูฝน

### Phase 9C — โมดูล Hotspot Risk, Recurrence & District Analysis
**เป้าหมาย:** ระบุพื้นที่เสี่ยงสูงและแยกแยะตามประเภทพื้นที่
1. **Top 10 High-Risk Tambon:** สร้าง Horizontal Bar Chart แสดง 10 ตำบลที่พบ Hotspot สูงสุด
2. **Recurrence Metric:** คานวณ "จำนวนวันที่เกิดไฟป่าซ้ำในตำบลเดิม" (Count distinct date per Tambon) นำเสนอเป็นตารางหรือกราฟแท่ง
3. **District & Forest Type Stacked Bar:** กราฟแท่งแกน X เป็น 'อำเภอ' แกน Y เป็นจำนวน Hotspot โดย Stack สีตาม 'ประเภทป่าอนุรักษ์' (อุทยานฯ vs เขตรักษาพันธุ์ฯ) เพื่อดูสัดส่วน
4. **Map Enhancement:** เพิ่มปุ่ม Toggle บนแผนที่ เพื่อสลับระหว่าง **Scatter Plot (จุดพิกัด)** และ **Density Heatmap (ความหนาแน่น)**

### Phase 9D — โมดูล Durian Correlation & Data Quality
**เป้าหมาย:** เทียบข้อมูลทุเรียนกับไฟป่า และแสดงข้อจำกัดข้อมูล
1. **Scatter Plot (Durian vs Hotspots):** แกน X = พื้นที่ปลูกทุเรียน (ไร่), แกน Y = จำนวน Hotspot, 1 จุด = 1 ตำบล (ตามข้อมูล Aggregate)
2. **Durian Trend Line:** กราฟเส้นแสดงการเปลี่ยนแปลงพื้นที่ทุเรียน พ.ศ. 2561-2568 (ดึงจาก Joined Table)
3. **🚨 การจัดการตรรกะ "ใกล้พื้นที่ปลูกทุเรียน":** 
   - *ข้อบังคับ:* ห้ามใช้ไลบรารีคำนวณระยะทางภูมิศาสตร์ (GIS Distance) เพราะเราไม่มี Polygon ของสวนทุเรียน 
   - *วิธีแก้:* ให้ใช้นิยามว่า **"ตำบลที่มีพื้นที่ปลูกทุเรียน > 0 ไร่"** ถือเป็นพื้นที่เป้าหมาย ให้แสดงจำนวน Hotspot ที่ตกอยู่ในกลุ่มตำบลนี้ เทียบกับกลุ่มตำบลที่ไม่มีทุเรียน
4. **Data Reliability Footer:** เพิ่มแถบข้อมูลด้านล่างสุดของ Dashboard แสดง:
   - "อัปเดตข้อมูลล่าสุด: [ดึงค่า Max Date จากข้อมูล]"
   - "จำนวนวันที่มีรายงานการตรวจพบ: [X] วัน"
   - "พิกัดซ้ำซ้อน (Duplicate coordinates): [X] จุด"

---

## 3. กฎเหล็กและข้อห้าม (Strict Constraints - MUST FOLLOW)
1. **Cross-Filtering is Mandatory:** ทุกกราฟ (KPI, แผนที่, Scatter, Bar, Line) ต้องผูกกับ Dash Callbacks (`@app.callback`) เมื่อผู้ใช้คลิกกราฟใดกราฟหนึ่ง กราฟอื่นต้องกรองข้อมูลตามทันที
2. **Single-Page Constraint:** ห้ามสร้าง Tab ใหม่ ให้ใช้ CSS Grid, Flexbox หรือ Bootstrap (Row/Col) ในการจัด Layout ให้สวยงามในหน้าเดียว (อาจทำกราฟให้เล็กลง หรือเรียงต่อกันด้านล่าง)
3. **Explicit Disclaimer (Causation Warning):** ต้องคงป้ายเตือนขนาดใหญ่ไว้เสมอว่า *"การพบจุดความร้อนในพื้นที่ปลูกทุเรียนสูง ไม่ได้หมายความว่าทุเรียนเป็นสาเหตุของไฟป่า และข้อมูลขอบเขตการปกครองไม่สามารถยืนยันความเสียหายของแปลงเกษตรได้"* ห้ามใช้คำพูดเชิงสาเหตุเด็ดขาด
4. **Data Integrity:** ห้ามแก้ไข Source CSV ให้ใช้ pandas จัดการใน `data_prep.py` หรือ Memory เท่านั้น

---

## 4. สิ่งที่ AI ต้องส่งมอบหลังทำเสร็จ (Expected Output from AI)
เมื่อแก้โค้ดเสร็จ ให้ AI สรุปรายงานดังนี้:
1. ไฟล์ใดบ้างที่ถูกแก้ไข (เช่น `app.py`, `data_prep.py`)
2. อธิบายวิธีที่ใช้ผูก Callback เพื่อทำ Global Cross-Filtering ของกราฟใหม่
3. หาก Layout แน่นเกินไป ให้เสนอแนะวิธีจัดวาง (เช่น การใส่ Accordion collapse) ให้ User ตัดสินใจ
4. **พิมพ์ข้อความ: "พร้อมให้รันและทดสอบ Phase 9 แล้วครับ"**