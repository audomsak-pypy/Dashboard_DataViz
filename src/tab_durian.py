"""
Tab 2: Durian Cultivation Analytics (Executive Dark Mode)
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.components import render_disclaimer_banner
from src.config import (
    COLOR_FIRE_PRIMARY,
    COLOR_FIRE_ACCENT,
    COLOR_FIRE_LIGHT,
    COLOR_BORDER_DARK,
    PLOTLY_CONFIG
)


def render_tab_durian(df_durian: pd.DataFrame, df_joined: pd.DataFrame):
    st.markdown("### ข้อมูลพื้นที่เพาะปลูกทุเรียน (Durian Cultivation)")
    st.caption("การสำรวจพื้นที่เพาะปลูกทุเรียน จังหวัดกาญจนบุรี (พ.ศ. 2561 - 2568) โดยสำนักงานเกษตรจังหวัดฯ")

    render_disclaimer_banner(kind="zero_missing")

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        years_avail = sorted(df_durian['พ.ศ.'].dropna().unique())
        selected_year = st.selectbox("เลือกปี พ.ศ. สำหรับวิเคราะห์", options=years_avail, index=len(years_avail)-1)

    with col_f2:
        all_amphoe = ["(ทั้งหมด)"] + sorted(df_durian['อำเภอ_norm'].dropna().unique())
        selected_amphoe = st.selectbox("กรองรายอำเภอ", options=all_amphoe)

    # Filtered dataset
    df_year = df_durian[df_durian['พ.ศ.'] == selected_year].copy()
    if selected_amphoe != "(ทั้งหมด)":
        df_year = df_year[df_year['อำเภอ_norm'] == selected_amphoe]

    # Metrics
    total_area = df_year['durian_area_rai'].dropna().sum()
    zero_count = (df_year['durian_area_rai'] == 0).sum()
    missing_count = df_year['durian_area_rai'].isna().sum()
    planted_count = (df_year['durian_area_rai'] > 0).sum()

    st.markdown("#### ตัวชี้วัดภาพรวม (Key Metrics)")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label=f"พื้นที่ปลูกรวมปี {selected_year}",
            value=f"{total_area:,.1f} ไร่"
        )
    with m2:
        st.metric(
            label="ตำบลที่มีการเพาะปลูก",
            value=f"{planted_count} ตำบล"
        )
    with m3:
        st.metric(
            label="ตำบลสำรวจแล้วไม่ปลูก (0.0)",
            value=f"{zero_count} ตำบล"
        )
    with m4:
        st.metric(
            label="ตำบลไม่มีข้อมูลสำรวจ (Null)",
            value=f"{missing_count} ตำบล"
        )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Historical trends (2561-2568)
    col_trend, col_dist = st.columns([1.2, 1])

    with col_trend:
        st.markdown("#### แนวโน้มพื้นที่ปลูกทุเรียนรายปี (พ.ศ. 2561 - 2568)")
        yearly_trend = df_durian.groupby('พ.ศ.', as_index=False).agg(
            total_rai=('durian_area_rai', 'sum')
        )

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=yearly_trend['พ.ศ.'],
            y=yearly_trend['total_rai'],
            name="พื้นที่ปลูก (ไร่)",
            marker_color=COLOR_FIRE_ACCENT,
            text=yearly_trend['total_rai'].apply(lambda x: f"{x:,.0f}"),
            textposition='auto'
        ))
        fig_trend.add_trace(go.Scatter(
            x=yearly_trend['พ.ศ.'],
            y=yearly_trend['total_rai'],
            name="แนวโน้ม",
            mode='lines+markers',
            line=dict(color=COLOR_FIRE_LIGHT, width=2.5)
        ))
        fig_trend.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=15, r=15, t=75, b=65),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickmode='linear', tick0=2561, dtick=1),
            yaxis=dict(title="พื้นที่เพาะปลูก (ไร่)"),
            title=dict(x=0.02, y=0.95, xanchor='left', yanchor='top'),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.22,
                xanchor="center",
                x=0.5,
                title_text=""
            )
        )
        st.plotly_chart(fig_trend, use_container_width=True, config=PLOTLY_CONFIG)

    with col_dist:
        st.markdown(f"#### สัดส่วนพื้นที่ปลูกจำแนกตามอำเภอ (ปี {selected_year})")
        amphoe_area = df_durian[df_durian['พ.ศ.'] == selected_year].groupby('อำเภอ_norm', as_index=False).agg(
            total_rai=('durian_area_rai', 'sum')
        ).sort_values('total_rai', ascending=True)

        fig_amp = px.bar(
            amphoe_area,
            x='total_rai',
            y='อำเภอ_norm',
            orientation='h',
            title=f"พื้นที่เพาะปลูกรายอำเภอ (ปี {selected_year})",
            labels={'total_rai': 'พื้นที่ปลูก (ไร่)', 'อำเภอ_norm': 'อำเภอ'},
            color='total_rai',
            color_continuous_scale="YlOrRd",
            template="plotly_dark"
        )
        fig_amp.update_layout(
            height=400,
            margin=dict(l=15, r=15, t=65, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=dict(x=0.02, y=0.96, xanchor='left', yanchor='top'),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_amp, use_container_width=True, config=PLOTLY_CONFIG)

    # Ranking Table
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown(f"#### ตารางจัดอันดับพื้นที่ปลูกทุเรียนรายตำบล (ปี พ.ศ. {selected_year})")

    table_data = df_year[['อำเภอ_norm', 'ตำบล_norm', 'durian_area_rai']].copy()
    table_data = table_data.sort_values(by='durian_area_rai', ascending=False, na_position='last')
    table_data['อันดับ'] = range(1, len(table_data) + 1)

    def _status_badge(val):
        if pd.isna(val):
            return "ไม่มีข้อมูลสำรวจ (Null)"
        elif val == 0:
            return "สำรวจแล้วไม่มีการปลูก (0.0 ไร่)"
        else:
            return f"เพาะปลูก {val:,.1f} ไร่"

    table_data['สถานะ'] = table_data['durian_area_rai'].apply(_status_badge)

    st.dataframe(
        table_data[['อันดับ', 'อำเภอ_norm', 'ตำบล_norm', 'durian_area_rai', 'สถานะ']].rename(
            columns={
                'อำเภอ_norm': 'อำเภอ',
                'ตำบล_norm': 'ตำบล',
                'durian_area_rai': 'พื้นที่เพาะปลูก (ไร่)'
            }
        ),
        use_container_width=True,
        height=420
    )
