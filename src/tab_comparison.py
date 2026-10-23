"""
Tab 3: Spatial & Temporal Comparison and Statistical Significance Testing (Executive Dark Mode)
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from scipy import stats
from src.components import render_disclaimer_banner
from src.config import (
    COLOR_FIRE_PRIMARY,
    COLOR_FIRE_ACCENT,
    COLOR_FIRE_LIGHT,
    COLOR_BORDER_DARK,
    PLOTLY_FIRE_SEQUENCE,
    PLOTLY_CONFIG
)


def render_tab_comparison(df_joined: pd.DataFrame):
    st.markdown("### การเปรียบเทียบเชิงพื้นที่และสถิติ (Spatial & Statistical Comparison)")
    st.caption("การวิเคราะห์ความสัมพันธ์เชิงปริมาณระดับตำบล และการทดสอบนัยสำคัญทางสถิติ (Mann-Whitney U Test)")

    # Mandatory Academic Disclaimer
    render_disclaimer_banner(kind="causal")

    years_comp = [2566, 2567, 2568]
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sel_year = st.selectbox(
            "เลือกปี พ.ศ. สำหรับเปรียบเทียบ (มีข้อมูลจุดความร้อนปี 2566 - 2568)",
            options=["ทุกปี (2566-2568)"] + years_comp
        )
    with col_f2:
        all_amphoe = ["(ทั้งหมด)"] + sorted(df_joined['อำเภอ_norm'].dropna().unique())
        sel_amp = st.selectbox("กรองเฉพาะอำเภอ", options=all_amphoe, key="comp_amphoe")

    comp_df = df_joined.copy()
    if sel_year != "ทุกปี (2566-2568)":
        comp_df = comp_df[comp_df['พ.ศ.'] == int(sel_year)]
    else:
        comp_df = comp_df[comp_df['พ.ศ.'].isin(years_comp)]

    if sel_amp != "(ทั้งหมด)":
        comp_df = comp_df[comp_df['อำเภอ_norm'] == sel_amp]

    # Section 1: Dual-Axis Line Chart
    st.markdown("#### 1. แนวโน้มเปรียบเทียบรายปี (Dual-Axis Comparison: 2566 - 2568)")

    annual_summary = df_joined[df_joined['พ.ศ.'].isin(years_comp)].groupby('พ.ศ.', as_index=False).agg(
        total_hotspots=('hotspot_count', 'sum'),
        total_durian=('durian_area_rai', 'sum')
    )

    fig_dual = go.Figure()
    fig_dual.add_trace(go.Bar(
        x=annual_summary['พ.ศ.'],
        y=annual_summary['total_durian'],
        name="พื้นที่ปลูกทุเรียน (ไร่)",
        marker_color=COLOR_FIRE_ACCENT,
        yaxis='y1',
        opacity=0.85,
        text=annual_summary['total_durian'].apply(lambda x: f"{x:,.0f} ไร่"),
        textposition='inside'
    ))
    fig_dual.add_trace(go.Scatter(
        x=annual_summary['พ.ศ.'],
        y=annual_summary['total_hotspots'],
        name="จำนวนจุดความร้อน (จุด)",
        marker=dict(color=COLOR_FIRE_PRIMARY, size=10),
        line=dict(color=COLOR_FIRE_PRIMARY, width=3),
        yaxis='y2',
        text=annual_summary['total_hotspots'].apply(lambda x: f"{x:,} จุด"),
        mode='lines+markers+text',
        textposition='top center'
    ))

    fig_dual.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=35, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="ปี พ.ศ.", tickmode='array', tickvals=years_comp),
        yaxis=dict(title="พื้นที่เพาะปลูกทุเรียน (ไร่)", side="left", showgrid=True),
        yaxis2=dict(title="จำนวนจุดความร้อน (จุด)", side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1)
    )
    st.plotly_chart(fig_dual, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Section 2 & 3: Bubble Chart & Mann-Whitney U Test
    col_bubble, col_stats = st.columns([1.2, 1])

    with col_bubble:
        st.markdown("#### 2. การกระจายตัวระดับตำบล (Bubble Chart)")

        valid_bubble = comp_df.dropna(subset=['durian_area_rai']).copy()

        fig_bubble = px.scatter(
            valid_bubble,
            x='durian_area_rai',
            y='hotspot_count',
            size='hotspot_count',
            color='อำเภอ_norm',
            hover_name='ตำบล_norm',
            hover_data=['อำเภอ_norm', 'พ.ศ.', 'durian_area_rai', 'hotspot_count'],
            size_max=32,
            title="จุดความร้อน vs พื้นที่ปลูกทุเรียนรายตำบล",
            labels={
                'durian_area_rai': 'พื้นที่ปลูกทุเรียน (ไร่)',
                'hotspot_count': 'จำนวนจุดความร้อน (จุด)',
                'อำเภอ_norm': 'อำเภอ'
            },
            color_discrete_sequence=PLOTLY_FIRE_SEQUENCE,
            template="plotly_dark"
        )
        fig_bubble.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=35, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_bubble, use_container_width=True, config=PLOTLY_CONFIG)

    with col_stats:
        st.markdown("#### 3. การทดสอบสมมติฐาน Mann-Whitney U Test")

        valid_stats = comp_df.dropna(subset=['durian_area_rai'])
        g_planted = valid_stats[valid_stats['durian_area_rai'] > 0]['hotspot_count']
        g_unplanted = valid_stats[valid_stats['durian_area_rai'] == 0]['hotspot_count']

        n1, n2 = len(g_planted), len(g_unplanted)

        if n1 > 0 and n2 > 0:
            res_u = stats.mannwhitneyu(g_planted, g_unplanted, alternative='two-sided')
            u_stat = res_u.statistic
            p_val = res_u.pvalue
            effect_size_r = 1.0 - (2.0 * u_stat) / (n1 * n2)

            st.markdown(f"""
            <div style="background-color: #161B22; padding: 16px; border-radius: 6px; border: 1px solid #30363D; border-left: 4px solid #FF7043;">
                <p style="margin: 0 0 8px 0; font-weight: 600; color: #F0F6FC;">กลุ่มตัวอย่าง (Sample Size):</p>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: #C9D1D9;">
                    <li>กลุ่มที่มีการปลูก (Area > 0): <b>{n1}</b> ตำบล (ค่าเฉลี่ย = {g_planted.mean():.1f}, มัธยฐาน = {g_planted.median():.0f})</li>
                    <li>กลุ่มที่ไม่มีการปลูก (Area == 0): <b>{n2}</b> ตำบล (ค่าเฉลี่ย = {g_unplanted.mean():.1f}, มัธยฐาน = {g_unplanted.median():.0f})</li>
                </ul>
                <hr style="border: 0; border-top: 1px solid #30363D; margin: 12px 0;"/>
                <p style="margin: 0 0 8px 0; font-weight: 600; color: #F0F6FC;">ผลการทดสอบทางสถิติ (Statistical Readout):</p>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.88rem; color: #C9D1D9;">
                    <li><b>Mann-Whitney U:</b> {u_stat:,.1f}</li>
                    <li><b>p-value:</b> {p_val:.4f} {'(มีนัยสำคัญทางสถิติที่ระดับ 0.05)' if p_val < 0.05 else '(ไม่มีนัยสำคัญ)'}</li>
                    <li><b>Effect Size (Rank-Biserial r):</b> {effect_size_r:.4f}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(
                """
                <div style="background-color: #1A1414; border: 1px solid #7F1D1D; padding: 10px 14px; 
                            border-radius: 6px; margin-top: 12px; font-size: 0.84rem; color: #FCA5A5;">
                    <b>การแปลผลเชิงสถิติ:</b> ผลการทดสอบแสดงความแตกต่างของการแจกแจงระดับตำบล 
                    แต่ <b>ไม่สามารถใช้สรุปความเป็นเหตุเป็นผลได้</b> เนื่องจากไม่มีพิกัดแปลงปลูกจริง
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("จำนวนข้อมูลไม่เพียงพอสำหรับการทดสอบทางสถิติทั้งสองกลุ่ม")

    # Section 4: Detailed Table
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("#### 4. ข้อมูลเปรียบเทียบระดับตำบล (Administrative Level Data)")

    table_comp = comp_df[['พ.ศ.', 'อำเภอ_norm', 'ตำบล_norm', 'durian_area_rai', 'hotspot_count', 'durian_status']].copy()
    table_comp = table_comp.rename(columns={
        'อำเภอ_norm': 'อำเภอ',
        'ตำบล_norm': 'ตำบล',
        'durian_area_rai': 'พื้นที่ปลูกทุเรียน (ไร่)',
        'hotspot_count': 'จำนวนจุดความร้อน (จุด)',
        'durian_status': 'สถานะการสำรวจ'
    })

    st.dataframe(
        table_comp,
        use_container_width=True,
        height=380
    )
