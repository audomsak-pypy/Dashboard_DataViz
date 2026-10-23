"""
Tab 3: Spatial & Temporal Comparison and Statistical Significance Testing.
Strict compliance with BRD.md Section 4 & Section 5 (No Causal Inference & Mann-Whitney U Test).
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats
from src.components import render_disclaimer_banner, create_gauge_meter
from src.config import (
    COLOR_FIRE_RED,
    COLOR_DURIAN_GREEN,
    COLOR_ACCENT_BLUE
)


def render_tab_comparison(df_joined: pd.DataFrame):
    st.markdown("### ⚖️ Tab 3: การเปรียบเทียบเชิงพื้นที่และเชิงเวลา (Spatial & Temporal Comparison)")
    st.caption("การวิเคราะห์ความสัมพันธ์เชิงปริมาณระดับตำบล และการทดสอบนัยสำคัญทางสถิติ (Non-parametric Mann-Whitney U Test)")

    # Mandatory Disclaimer required by BRD
    render_disclaimer_banner(kind="causal")

    # Filter year for comparison (2566-2568 have wildfire data)
    years_comp = [2566, 2567, 2568]
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sel_year = st.selectbox(
            "📅 เลือกปี พ.ศ. ที่ต้องการเปรียบเทียบ (มีข้อมูลจุดความร้อนปี 2566 - 2568)",
            options=["ทุกปี (2566-2568)"] + years_comp
        )
    with col_f2:
        all_amphoe = ["(ทั้งหมด)"] + sorted(df_joined['อำเภอ_norm'].dropna().unique())
        sel_amp = st.selectbox("🏛️ กรองเฉพาะอำเภอ", options=all_amphoe, key="comp_amphoe")

    # Filtered dataframe
    comp_df = df_joined.copy()
    if sel_year != "ทุกปี (2566-2568)":
        comp_df = comp_df[comp_df['พ.ศ.'] == int(sel_year)]
    else:
        comp_df = comp_df[comp_df['พ.ศ.'].isin(years_comp)]

    if sel_amp != "(ทั้งหมด)":
        comp_df = comp_df[comp_df['อำเภอ_norm'] == sel_amp]

    # --- SECTION 1: DUAL-AXIS LINE CHART (พ.ศ. 2566-2568) ---
    st.markdown("#### 📈 1. แนวโน้มเปรียบเทียบรายปี (Dual-Axis Comparison: 2566 - 2568)")
    st.caption("หมายเหตุ: พ.ศ. 2566 เริ่มบันทึกปลายปี (พ.ย.-ธ.ค.) และ พ.ศ. 2568 บันทึกถึง ส.ค. จึงควรระมัดระวังในการเปรียบเทียบฤดูกาล")

    annual_summary = df_joined[df_joined['พ.ศ.'].isin(years_comp)].groupby('พ.ศ.', as_index=False).agg(
        total_hotspots=('hotspot_count', 'sum'),
        total_durian=('durian_area_rai', 'sum')
    )

    fig_dual = go.Figure()
    # Bar for Durian Area
    fig_dual.add_trace(go.Bar(
        x=annual_summary['พ.ศ.'],
        y=annual_summary['total_durian'],
        name="พื้นที่ปลูกทุเรียน (ไร่)",
        marker_color=COLOR_DURIAN_GREEN,
        yaxis='y1',
        opacity=0.7,
        text=annual_summary['total_durian'].apply(lambda x: f"{x:,.0f} ไร่"),
        textposition='inside'
    ))
    # Line for Hotspot Count
    fig_dual.add_trace(go.Scatter(
        x=annual_summary['พ.ศ.'],
        y=annual_summary['total_hotspots'],
        name="จำนวนจุดความร้อน (จุด)",
        marker=dict(color=COLOR_FIRE_RED, size=10),
        line=dict(color=COLOR_FIRE_RED, width=3),
        yaxis='y2',
        text=annual_summary['total_hotspots'].apply(lambda x: f"{x:,} จุด"),
        mode='lines+markers+text',
        textposition='top center'
    ))

    fig_dual.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis=dict(title="ปี พ.ศ.", tickmode='array', tickvals=years_comp),
        yaxis=dict(title="พื้นที่เพาะปลูกทุเรียน (ไร่)", side="left", showgrid=True),
        yaxis2=dict(title="จำนวนจุดความร้อน (จุด)", side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1)
    )
    st.plotly_chart(fig_dual, use_container_width=True)

    st.markdown("---")

    # --- SECTION 2: BUBBLE CHART (HOTSPOT VS DURIAN AREA BY TAMBON) ---
    col_bubble, col_stats = st.columns([1.2, 1])

    with col_bubble:
        st.markdown("#### 🫧 2. แผนภูมิฟองสบู่เปรียบเทียบระดับตำบล (Bubble Chart)")
        st.caption("แกน X: พื้นที่ปลูกทุเรียน (ไร่) | แกน Y: จำนวนจุดความร้อน (จุด) | ขนาด: จุดความร้อน")

        # Exclude null durian for scatter
        valid_bubble = comp_df.dropna(subset=['durian_area_rai']).copy()

        fig_bubble = px.scatter(
            valid_bubble,
            x='durian_area_rai',
            y='hotspot_count',
            size='hotspot_count',
            color='อำเภอ_norm',
            hover_name='ตำบล_norm',
            hover_data=['อำเภอ_norm', 'พ.ศ.', 'durian_area_rai', 'hotspot_count'],
            size_max=35,
            title="ความสัมพันธ์ระดับตำบล: จุดความร้อน vs พื้นที่ทุเรียน",
            labels={
                'durian_area_rai': 'พื้นที่ปลูกทุเรียน (ไร่)',
                'hotspot_count': 'จำนวนจุดความร้อน (จุด)',
                'อำเภอ_norm': 'อำเภอ'
            }
        )
        fig_bubble.update_layout(height=420, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_bubble, use_container_width=True)

    # --- SECTION 3: MANN-WHITNEY U TEST (STRICT BRD REQUIREMENT) ---
    with col_stats:
        st.markdown("#### 🧪 3. การทดสอบสมมติฐาน Mann-Whitney U Test")
        st.caption("เปรียบเทียบการกระจายของ `hotspot_count` ระหว่างตำบลที่ปลูกทุเรียน vs ไม่ปลูก")

        valid_stats = comp_df.dropna(subset=['durian_area_rai'])
        g_planted = valid_stats[valid_stats['durian_area_rai'] > 0]['hotspot_count']
        g_unplanted = valid_stats[valid_stats['durian_area_rai'] == 0]['hotspot_count']

        n1, n2 = len(g_planted), len(g_unplanted)

        if n1 > 0 and n2 > 0:
            res_u = stats.mannwhitneyu(g_planted, g_unplanted, alternative='two-sided')
            u_stat = res_u.statistic
            p_val = res_u.pvalue
            # Effect size: Rank-biserial correlation r = 1 - (2*U / (n1*n2))
            effect_size_r = 1.0 - (2.0 * u_stat) / (n1 * n2)

            st.markdown(f"""
            <div style="background-color: #F8F9FA; padding: 15px; border-radius: 8px; border-left: 5px solid #2196F3;">
                <p><b>กลุ่มตัวอย่าง (Sample Size):</b></p>
                <ul>
                    <li>กลุ่มมีการปลูกทุเรียน (Area > 0): <b>{n1}</b> ตำบล (ค่าเฉลี่ย = {g_planted.mean():.1f}, ค่ามัธยฐาน = {g_planted.median():.0f})</li>
                    <li>กลุ่มไม่มีการปลูก (Area == 0): <b>{n2}</b> ตำบล (ค่าเฉลี่ย = {g_unplanted.mean():.1f}, ค่ามัธยฐาน = {g_unplanted.median():.0f})</li>
                </ul>
                <hr style="margin: 8px 0;"/>
                <p><b>ผลการทดสอบทางสถิติ:</b></p>
                <ul>
                    <li><b>Mann-Whitney U Statistic:</b> {u_stat:,.1f}</li>
                    <li><b>p-value:</b> {p_val:.4f} {'(มีนัยสำคัญทางสถิติที่ระดับ 0.05)' if p_val < 0.05 else '(ไม่มีนัยสำคัญทางสถิติ)'}</li>
                    <li><b>Effect Size (Rank-Biserial r):</b> {effect_size_r:.4f}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.info(
                "📌 **การแปลผลเชิงสถิติ:** การทดสอบนี้แสดงความแตกต่างในการกระจายตัวของจำนวนจุดความร้อนระดับตำบล "
                "แต่ **ไม่สามารถใช้ระบุความเป็นเหตุเป็นผล (Causation)** ได้ เนื่องจากการเกิดจุดความร้อนขึ้นกับปัจจัยภูมิประเทศ "
                "สภาพอากาศ และพื้นที่ป่าอนุรักษ์ในแต่ละตำบล"
            )
        else:
            st.warning("จำนวนข้อมูลไม่เพียงพอสำหรับคำนวณการทดสอบทั้งสองกลุ่ม")

    # --- SECTION 4: DETAILED COMPARISON TABLE (WIREFRAME BOTTOM) ---
    st.markdown("---")
    st.markdown("#### 📋 4. ตารางเปรียบเทียบรายตำบลแบบละเอียด (Detailed Administrative Level Data)")

    table_comp = comp_df[['พ.ศ.', 'อำเภอ_norm', 'ตำบล_norm', 'durian_area_rai', 'hotspot_count', 'durian_status']].copy()
    table_comp = table_comp.rename(columns={
        'อำเภอ_norm': 'อำเภอ',
        'ตำบล_norm': 'ตำบล',
        'durian_area_rai': 'พื้นที่ปลูกทุเรียน (ไร่)',
        'hotspot_count': 'จำนวนจุดความร้อน (จุด)',
        'durian_status': 'สถานะการสำรวจ'
    })

    st.dataframe(
        table_comp.style.format({
            'พื้นที่ปลูกทุเรียน (ไร่)': lambda x: f"{x:,.1f}" if pd.notna(x) else "ไม่มีข้อมูล (Null)",
            'จำนวนจุดความร้อน (จุด)': "{:,}"
        }).background_gradient(subset=['จำนวนจุดความร้อน (จุด)'], cmap='OrRd'),
        use_container_width=True,
        height=400
    )
