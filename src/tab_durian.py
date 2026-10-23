"""
Tab 2: Durian Cultivation Overview
Strict compliance with BRD.md Section 4 & Research Questions 2, 5.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.components import render_disclaimer_banner, create_gauge_meter
from src.config import (
    COLOR_DURIAN_GREEN,
    COLOR_DURIAN_YELLOW,
    COLOR_ACCENT_BLUE
)


def render_tab_durian(df_durian: pd.DataFrame, df_joined: pd.DataFrame):
    st.markdown("### 🍈 Tab 2: ข้อมูลพื้นที่เพาะปลูกทุเรียน (Durian Cultivation)")
    st.caption("สำรวจพื้นที่เพาะปลูกทุเรียนในจังหวัดกาญจนบุรี (พ.ศ. 2561 - 2568) โดยสำนักงานเกษตรจังหวัดฯ")

    render_disclaimer_banner(kind="zero_missing")

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        years_avail = sorted(df_durian['พ.ศ.'].dropna().unique())
        selected_year = st.selectbox("📅 เลือกปี พ.ศ. สำหรับจัดอันดับ", options=years_avail, index=len(years_avail)-1)

    with col_f2:
        all_amphoe = ["(ทั้งหมด)"] + sorted(df_durian['อำเภอ_norm'].dropna().unique())
        selected_amphoe = st.selectbox("🏛️ กรองรายอำเภอ", options=all_amphoe)

    # Filtered dataset for selected year
    df_year = df_durian[df_durian['พ.ศ.'] == selected_year].copy()
    if selected_amphoe != "(ทั้งหมด)":
        df_year = df_year[df_year['อำเภอ_norm'] == selected_amphoe]

    # Metrics
    total_area = df_year['durian_area_rai'].dropna().sum()
    zero_count = (df_year['durian_area_rai'] == 0).sum()
    missing_count = df_year['durian_area_rai'].isna().sum()
    planted_count = (df_year['durian_area_rai'] > 0).sum()

    st.markdown("#### 📊 ตัวชี้วัดภาพรวมพื้นที่ปลูกทุเรียน")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label=f"🌱 พื้นที่ปลูกรวมปี {selected_year}",
            value=f"{total_area:,.1f} ไร่"
        )
    with m2:
        st.metric(
            label="✅ ตำบลที่มีการเพาะปลูก",
            value=f"{planted_count} ตำบล"
        )
    with m3:
        st.metric(
            label="⚪ ตำบลสำรวจแล้วไม่ปลูก (0.0)",
            value=f"{zero_count} ตำบล",
            help="มีรายงานการสำรวจและบันทึกเป็น 0.0 ไร่"
        )
    with m4:
        st.metric(
            label="⚠️ ตำบลไม่มีข้อมูลสำรวจ (Null)",
            value=f"{missing_count} ตำบล",
            help="ไม่มีรายงานในรอบสำรวจนั้น"
        )

    st.markdown("---")

    # --- HISTORICAL TRENDS (พ.ศ. 2561-2568) (RQ5) ---
    col_trend, col_dist = st.columns([1.2, 1])

    with col_trend:
        st.markdown("#### 📈 แนวโน้มพื้นที่ปลูกทุเรียนรวมรายปี (พ.ศ. 2561 - 2568 - RQ5)")
        yearly_trend = df_durian.groupby('พ.ศ.', as_index=False).agg(
            total_rai=('durian_area_rai', 'sum'),
            planted_tambons=('durian_area_rai', lambda s: (s > 0).sum())
        )

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=yearly_trend['พ.ศ.'],
            y=yearly_trend['total_rai'],
            name="พื้นที่ปลูก (ไร่)",
            marker_color=COLOR_DURIAN_GREEN,
            text=yearly_trend['total_rai'].apply(lambda x: f"{x:,.0f}"),
            textposition='auto'
        ))
        fig_trend.add_trace(go.Scatter(
            x=yearly_trend['พ.ศ.'],
            y=yearly_trend['total_rai'],
            name="เส้นแนวโน้ม",
            mode='lines+markers',
            line=dict(color=COLOR_DURIAN_YELLOW, width=3)
        ))
        fig_trend.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=35, b=10),
            xaxis=dict(tickmode='linear', tick0=2561, dtick=1),
            yaxis=dict(title="พื้นที่เพาะปลูก (ไร่)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_dist:
        st.markdown(f"#### 🏛️ สัดส่วนพื้นที่ปลูกจำแนกตามอำเภอ (ปี {selected_year})")
        amphoe_area = df_durian[df_durian['พ.ศ.'] == selected_year].groupby('อำเภอ_norm', as_index=False).agg(
            total_rai=('durian_area_rai', 'sum')
        ).sort_values('total_rai', ascending=True)

        fig_amp = px.bar(
            amphoe_area,
            x='total_rai',
            y='อำเภอ_norm',
            orientation='h',
            title=f"พื้นที่เพาะปลูกทุเรียนรายอำเภอ (ปี พ.ศ. {selected_year})",
            labels={'total_rai': 'พื้นที่ปลูก (ไร่)', 'อำเภอ_norm': 'อำเภอ'},
            color='total_rai',
            color_continuous_scale="Greens"
        )
        fig_amp.update_layout(height=380, margin=dict(l=10, r=10, t=35, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_amp, use_container_width=True)

    # --- RANKING DATA TABLE (RQ2) WITH ZERO VS MISSING HIGHLIGHTING ---
    st.markdown("---")
    st.markdown(f"#### 📋 ตารางจัดอันดับพื้นที่ปลูกทุเรียนรายตำบล (ปี พ.ศ. {selected_year} - RQ2)")
    st.caption("สังเกต: มีการแยกสีชัดเจนระหว่างตำบลที่มีการปลูก, ตำบลที่สำรวจแล้วเป็น 0.0 ไร่, และตำบลที่ไม่มีข้อมูลสำรวจ (Null)")

    # Prepare table with styling
    table_data = df_year[['อำเภอ_norm', 'ตำบล_norm', 'durian_area_rai']].copy()
    table_data = table_data.sort_values(by='durian_area_rai', ascending=False, na_position='last')
    table_data['อันดับ'] = range(1, len(table_data) + 1)

    # Format status text
    def _status_badge(val):
        if pd.isna(val):
            return "⚠️ ไม่มีข้อมูลสำรวจ (Null)"
        elif val == 0:
            return "⚪ สำรวจแล้วไม่มีการปลูก (0.0 ไร่)"
        else:
            return f"🟢 ปลูก {val:,.1f} ไร่"

    table_data['สถานะการสำรวจ'] = table_data['durian_area_rai'].apply(_status_badge)

    # Add historical trend per tambon
    st.dataframe(
        table_data[['อันดับ', 'อำเภอ_norm', 'ตำบล_norm', 'durian_area_rai', 'สถานะการสำรวจ']].rename(
            columns={
                'อำเภอ_norm': 'อำเภอ',
                'ตำบล_norm': 'ตำบล',
                'durian_area_rai': 'พื้นที่เพาะปลูก (ไร่)'
            }
        ).style.format({
            'พื้นที่เพาะปลูก (ไร่)': lambda x: f"{x:,.1f}" if pd.notna(x) else "—"
        }).background_gradient(subset=['พื้นที่เพาะปลูก (ไร่)'], cmap='YlGn'),
        use_container_width=True,
        height=450
    )
