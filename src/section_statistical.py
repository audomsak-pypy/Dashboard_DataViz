"""
Section: Statistical Analysis & Disclaimers (Mann-Whitney U Test & Spatial Comparison).
Kanchanaburi Wildfire & Durian Spatial Analytics.
Fully connected to Centralized Filtered Data.
"""

import streamlit as st
import pandas as pd
from scipy import stats


def render_statistical_summary_bottom(filtered_joined: pd.DataFrame):
    """
    แสดงผลการเปรียบเทียบเชิงสถิติ (Mann-Whitney U Test และ Effect Size)
    โดยแบ่งกลุ่มตามมัธยฐานพื้นที่ปลูกทุเรียนจริง (Median Split) เพื่อแก้ปัญหาความบิดเบือนของกลุ่มตัวอย่าง
    พร้อมระบุสัดส่วนตำบลที่พบจุดความร้อน (Proportion of tambons with wildfire)
    หมายเหตุ: นำกล่องเตือนขอบส้มซ้ำซ้อนออก คงไว้เฉพาะกล่องหลักที่บนสุดของหน้าแดชบอร์ด
    """
    valid_stats = filtered_joined.dropna(subset=['durian_area_rai']).copy()
    planted = valid_stats[valid_stats['durian_area_rai'] > 0].copy()

    years_in_data = sorted(valid_stats['พ.ศ.'].dropna().unique())
    if len(years_in_data) > 1:
        years_label = f"พ.ศ. {years_in_data[0]} - {years_in_data[-1]}"
    elif len(years_in_data) == 1:
        years_label = f"พ.ศ. {years_in_data[0]}"
    else:
        years_label = "พ.ศ. 2566 - 2568"

    n_total = len(planted)
    if n_total >= 4:
        med_rai = float(planted['durian_area_rai'].median())
        g_high = planted[planted['durian_area_rai'] >= med_rai]['hotspot_count']
        g_low = planted[planted['durian_area_rai'] < med_rai]['hotspot_count']

        n1, n2 = len(g_high), len(g_low)
        med1 = float(g_high.median()) if n1 > 0 else 0.0
        med2 = float(g_low.median()) if n2 > 0 else 0.0
        mean1 = float(g_high.mean()) if n1 > 0 else 0.0
        mean2 = float(g_low.mean()) if n2 > 0 else 0.0

        # Proportion of tambons with wildfire (hotspot > 0)
        fire_cnt1 = int((g_high > 0).sum())
        fire_cnt2 = int((g_low > 0).sum())
        fire_pct1 = (fire_cnt1 / n1 * 100) if n1 > 0 else 0.0
        fire_pct2 = (fire_cnt2 / n2 * 100) if n2 > 0 else 0.0

        try:
            u_stat, p_val = stats.mannwhitneyu(g_high, g_low, alternative='two-sided')
            r_rb = 1.0 - (2.0 * u_stat / (n1 * n2)) if (n1 * n2) > 0 else 0.0
            stat_headline = f"ผลการวิเคราะห์ทางสถิติ: Mann-Whitney U = {u_stat:,.1f}, p-value = {p_val:.4f} (Effect Size r = {abs(r_rb):.2f})"
            stat_body = (
                f"การทดสอบเปรียบเทียบตำบลกลุ่มพื้นที่ทุเรียนสูง (≥ {med_rai:,.1f} ไร่) กับกลุ่มพื้นที่ทุเรียนต่ำ (< {med_rai:,.1f} ไร่) "
                f"พบสัดส่วนตำบลที่ตรวจพบไฟป่าต่างกัน {abs(fire_pct1 - fire_pct2):.1f}% "
                f"อย่างไรก็ดี ความแตกต่างนี้สะท้อนลักษณะทางภูมิศาสตร์และขนาดพื้นที่ของตำบลในเขตเทือกเขา (Spatial Confounding) "
                f"เนื่องจากข้อมูลจุดความร้อนส่วนใหญ่กระจุกตัวในป่าอนุรักษ์ส่วนลึก จึงไม่สามารถสรุปความสัมพันธ์เชิงสาเหตุ (Causality) ได้"
            )
        except Exception:
            stat_headline = "ผลการวิเคราะห์ทางสถิติ: ไม่สามารถคำนวณสถิติสำหรับกลุ่มข้อมูลปัจจุบันได้"
            stat_body = "ค่าตัวแปรในกลุ่มข้อมูลมีความแปรปรวนเป็นศูนย์หรือขนาดตัวอย่างจำกัด"
    else:
        n1, n2 = len(planted), 0
        med_rai = 0.0
        med1, med2 = 0.0, 0.0
        mean1, mean2 = 0.0, 0.0
        fire_cnt1, fire_cnt2 = 0, 0
        fire_pct1, fire_pct2 = 0.0, 0.0
        stat_headline = "ผลการวิเคราะห์ทางสถิติ: ขนาดตัวอย่างในตัวกรองปัจจุบันมีจำกัด"
        stat_body = "แนะนำให้เลือกภาพรวมทุกอำเภอ หรือเลือกช่วงปีเพิ่มเติม เพื่อให้มีขนาดตัวอย่างเพียงพอต่อการทดสอบทางสถิติ"

    # กล่องผลการวิเคราะห์เชิงสถิติ (ขอบสีฟ้า / Dark UI) - ไม่มีกล่องส้มซ้ำซ้อน
    st.markdown(f"""
    <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 18px 22px; margin-bottom: 24px;">
        <div style="color: #FF7043; font-weight: 700; font-size: 0.95rem; margin-bottom: 10px;">
            รายละเอียดกลุ่มข้อมูล และผลการทดสอบสมมติฐานทางสถิติ (Mann-Whitney U Test & Spatial Comparison)
        </div>
        <div style="color: #F0F6FC; font-weight: 600; font-size: 0.88rem; margin-bottom: 8px;">
            ข้อเท็จจริงเชิงพื้นที่ระดับตำบล ({years_label}) - แบ่งกลุ่มตามมัธยฐานพื้นที่เพาะปลูก ({med_rai:,.1f} ไร่):
        </div>
        <ul style="color: #C9D1D9; font-size: 0.84rem; line-height: 1.6; margin-bottom: 14px;">
            <li><b>กลุ่มพื้นที่ทุเรียนสูง ≥ {med_rai:,.1f} ไร่ (n = {n1} ตำบล-ปี):</b> พบไฟป่า {fire_cnt1}/{n1} ตำบล ({fire_pct1:.1f}%), ค่ามัธยฐาน {med1:.1f} จุด, ค่าเฉลี่ย {mean1:.1f} จุด</li>
            <li><b>กลุ่มพื้นที่ทุเรียนต่ำ < {med_rai:,.1f} ไร่ (n = {n2} ตำบล-ปี):</b> พบไฟป่า {fire_cnt2}/{n2} ตำบล ({fire_pct2:.1f}%), ค่ามัธยฐาน {med2:.1f} จุด, ค่าเฉลี่ย {mean2:.1f} จุด</li>
            <li><b>ความต่างของสัดส่วนตำบลที่พบไฟป่า (Effect Size):</b> {abs(fire_pct1 - fire_pct2):.1f}% (กลุ่มสูงพบไฟป่า {fire_pct1:.1f}% เทียบกับ {fire_pct2:.1f}%)</li>
        </ul>
        <div style="background-color: #0E1117; border: 1px solid #30363D; border-left: 3px solid #38BDF8; border-radius: 6px; padding: 12px 16px;">
            <div style="color: #38BDF8; font-weight: 600; font-size: 0.84rem; margin-bottom: 4px;">
                {stat_headline}
            </div>
            <div style="color: #8B949E; font-size: 0.82rem; line-height: 1.5;">
                {stat_body}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
