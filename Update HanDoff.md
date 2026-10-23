## 📍 Phase 3 — Application Foundation & Single-Page Layout
**เป้าหมาย:** สร้างโครงสร้างแอปพลิเคชันหน้าเดียว (Single-Page) แบบ Grid/Responsive และเตรียม Data Store สำหรับรองรับ Cross-Filtering
*   จัดวาง Layout โดยแบ่งเป็น แผงควบคุมตัวกรอง (Global Filters), แผนที่ (Map), ตารางข้อมูล (Data Table) และกราฟสถิติ (Charts) ในหน้าเดียวกันทั้งหมด
*   **ห้ามทำระบบ Multi-tabs:** ทุกองค์ประกอบต้องอยู่รวมกันอย่างเป็นระเบียบ

## 📍 Phase 4 — Global Cross-Filtering Implementation (Core Interactivity)
**เป้าหมาย:** สร้าง Plotly Dash Callbacks เพื่อผูกทุก UI เข้าด้วยกัน (Interactive Dashboard)
*   สร้าง `Callback` หลักที่รับ Input จาก: 
    1. Dropdowns/DatePickers (Global Filters)
    2. `clickData` หรือ `selectedData` จาก ScatterMap (เมื่อผู้ใช้จิ้มจุดบนแผนที่)
    3. `active_cell` หรือ `selected_rows` จากตารางพื้นที่ปลูกทุเรียน
*   **Action:** เมื่อเกิด Input ข้อใดข้อหนึ่ง ให้ Dashboard อัปเดตตัวเลข KPI, แผนที่, กราฟ Hotspot, และกราฟทุเรียน ให้สอดคล้องกับพื้นที่หรือเงื่อนไขที่ถูกเลือกแบบ Real-time
*   **Approval Gate:** ให้ผู้ใช้ทดสอบว่าคลิกตารางแล้วแผนที่เปลี่ยน หรือคลิกแผนที่แล้วตารางเปลี่ยนจริงหรือไม่ก่อนไปทำ Phase ถัดไป

## 📍 Phase 5 — UI & Visualizations Development
**เป้าหมาย:** สร้างกราฟและแผนที่ให้ครบตาม BRD โดยใช้ Data Model ที่ Clean แล้ว
*   สร้าง ScatterMap แสดงจุด Hotspot ทั้งจังหวัด (แสดงข้อจำกัด CRS)
*   สร้างตารางจัดอันดับพื้นที่ปลูกทุเรียน (แยกการแสดงผล 0 กับ Missing ให้ชัด)
*   สร้าง Bar Chart หรือ Dual-axis Chart สำหรับวิเคราะห์แนวโน้มเวลา (รายเดือน/รายชั่วโมง)
*   **The Simple Comparison Chart:** สร้าง Bar Chart เปรียบเทียบ "ค่าเฉลี่ยจุดความร้อนต่อตำบล" (Hotspots per Tambon) ระหว่างกลุ่มที่มีพื้นที่ปลูกทุเรียน (>0) และไม่มีพื้นที่ปลูกทุเรียน (==0) เลิกใช้ Mann-Whitney U test แต่ให้ใส่ข้อความ Text อธิบายผลลัพธ์เฉลี่ยแทน
*   **Disclaimer:** ป้ายเตือนว่า "การเปรียบเทียบใช้ขอบเขตการปกครอง ไม่ได้หมายความว่าไฟเกิดในแปลงปลูก และไม่สามารถสรุปความเป็นเหตุเป็นผลได้" ต้องเด่นชัดบนหน้าจอ

*(Phase 1, 2 และ 7 ให้ยึดตาม HANDOFF.md ฉบับเดิม)*