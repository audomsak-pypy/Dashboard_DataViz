"""
Tab 1: Hotspot Spatial & Temporal Analytics (Executive Dark Mode)
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.components import render_disclaimer_banner, create_gauge_meter
from src.config import (
    COLOR_FIRE_PRIMARY,
    COLOR_FIRE_ACCENT,
    COLOR_FIRE_LIGHT,
    COLOR_BORDER_DARK,
    COLOR_MUTED_GRAY,
    PLOTLY_FIRE_SEQUENCE,
    PLOTLY_CONFIG
)


def render_tab_hotspots(df_events: pd.DataFrame, total_expected: int):
    st.markdown("### ภาพรวมจุดความร้อนในพื้นที่ป่าอนุรักษ์ (Hotspots Overview)")
    st.caption("การกระจายตัวเชิงพื้นที่และเชิงเวลาของจุดความร้อนในเขตป่าอนุรักษ์ จังหวัดกาญจนบุรี")

    # Executive Summary & Dashboard Guide
    with st.expander("Executive Summary & Dashboard Guide", expanded=True):
        st.markdown("""
        <div style="color: #F0F6FC; font-size: 0.9rem; line-height: 1.6;">
            <div style="margin-bottom: 12px;">
                <span style="color: #FF7043; font-weight: 600; font-size: 0.92rem;">Dashboard Objective:</span><br/>
                สำรวจและเปรียบเทียบข้อมูลจุดความร้อน (Hotspots) ในพื้นที่ป่าอนุรักษ์ กับข้อมูลพื้นที่เพาะปลูกทุเรียนในจังหวัดกาญจนบุรี ในมิติเชิงพื้นที่ (Spatial) และเชิงเวลา (Temporal) โดยมุ่งเน้นการแสดงข้อเท็จจริงอย่างโปร่งใส และปราศจากการสรุปข้อสมมติฐานเชิงสาเหตุ (Strictly without making causal inferences)
            </div>
            <div style="border-top: 1px solid #30363D; padding-top: 12px; margin-top: 10px;">
                <span style="color: #FFA726; font-weight: 600; font-size: 0.92rem;">Analytical Guide (Chart-to-Question Mapping)</span>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-top: 10px;">
                    <div style="background-color: #0E1117; border: 1px solid #30363D; border-left: 3px solid #E53935; padding: 12px 14px; border-radius: 6px;">
                        <div style="color: #E53935; font-weight: 600; font-size: 0.85rem; margin-bottom: 6px;">Spatial & Location Analysis</div>
                        <div style="color: #C9D1D9; font-size: 0.82rem; line-height: 1.45;">
                            แผนที่พิกัด (Geographic Map) และแผนที่ความหนาแน่น (Heatmap) ใช้ตอบคำถามเกี่ยวกับพื้นที่วิกฤต (Critical Risk Areas) และการกระจุกตัวของจุดความร้อนรายตำบล/เขตป่าอนุรักษ์
                        </div>
                    </div>
                    <div style="background-color: #0E1117; border: 1px solid #30363D; border-left: 3px solid #FF7043; padding: 12px 14px; border-radius: 6px;">
                        <div style="color: #FF7043; font-weight: 600; font-size: 0.85rem; margin-bottom: 6px;">Temporal Trends Analysis</div>
                        <div style="color: #C9D1D9; font-size: 0.82rem; line-height: 1.45;">
                            แผนภูมิรายเดือน (Seasonal Wave) และรายชั่วโมง (Hourly Breakdown) ใช้ตอบคำถามเกี่ยวกับช่วงพีคของฤดูกาลเกิดไฟป่า (Peak Fire Seasons) และรูปแบบการเกิดรายวัน (Daily Patterns)
                        </div>
                    </div>
                    <div style="background-color: #0E1117; border: 1px solid #30363D; border-left: 3px solid #FFA726; padding: 12px 14px; border-radius: 6px;">
                        <div style="color: #FFA726; font-weight: 600; font-size: 0.85rem; margin-bottom: 6px;">Statistical & Comparative Analysis (Tab 3)</div>
                        <div style="color: #C9D1D9; font-size: 0.82rem; line-height: 1.45;">
                            การทดสอบ Mann-Whitney U Test และแผนภูมิเปรียบเทียบสองแกน (Dual-Axis) ใช้ตอบคำถามว่ามีความแตกต่างอย่างมีนัยสำคัญของจุดความร้อนระหว่างตำบลที่มีและไม่มีการปลูกทุเรียนหรือไม่
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    render_disclaimer_banner(kind="crs")

    # Filters
    with st.expander("ตัวกรองข้อมูล (Data Filters)", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        with col_f1:
            all_years = sorted(df_events['พ.ศ.'].dropna().unique())
            selected_years = st.multiselect("ปี พ.ศ.", options=all_years, default=all_years)

        with col_f2:
            all_amphoe = sorted(df_events['อำเภอ_norm'].dropna().unique())
            selected_amphoe = st.multiselect("อำเภอ", options=all_amphoe, default=[])

        with col_f3:
            if selected_amphoe:
                available_tambon = sorted(
                    df_events[df_events['อำเภอ_norm'].isin(selected_amphoe)]['ตำบล_norm'].dropna().unique()
                )
            else:
                available_tambon = sorted(df_events['ตำบล_norm'].dropna().unique())
            selected_tambon = st.multiselect("ตำบล", options=available_tambon, default=[])

        with col_f4:
            all_forest_types = sorted(df_events['ประเภทป่าอนุรักษ์'].dropna().unique())
            selected_forest_types = st.multiselect("ประเภทป่าอนุรักษ์", options=all_forest_types, default=[])

    # Filter logic
    filtered_df = df_events.copy()
    if selected_years:
        filtered_df = filtered_df[filtered_df['พ.ศ.'].isin(selected_years)]
    if selected_amphoe:
        filtered_df = filtered_df[filtered_df['อำเภอ_norm'].isin(selected_amphoe)]
    if selected_tambon:
        filtered_df = filtered_df[filtered_df['ตำบล_norm'].isin(selected_tambon)]
    if selected_forest_types:
        filtered_df = filtered_df[filtered_df['ประเภทป่าอนุรักษ์'].isin(selected_forest_types)]

    count_filtered = len(filtered_df)

    # Executive Key Indicators
    st.markdown("#### ตัวชี้วัดสำคัญ (Key Metrics)")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns([1.1, 1.1, 1.1, 1.1])

    with kpi_col1:
        fig_g1 = create_gauge_meter(
            value=count_filtered,
            max_val=total_expected,
            title="จุดความร้อนในตัวกรอง",
            unit="จุด",
            color=COLOR_FIRE_PRIMARY
        )
        st.plotly_chart(fig_g1, use_container_width=True, config=PLOTLY_CONFIG)

    with kpi_col2:
        pct_of_total = (count_filtered / total_expected * 100) if total_expected > 0 else 0
        fig_g2 = create_gauge_meter(
            value=round(pct_of_total, 1),
            max_val=100,
            title="สัดส่วนเทียบทั้งจังหวัด",
            unit="%",
            color=COLOR_FIRE_ACCENT
        )
        st.plotly_chart(fig_g2, use_container_width=True, config=PLOTLY_CONFIG)

    with kpi_col3:
        top_amp = filtered_df['อำเภอ_norm'].value_counts().index[0] if count_filtered > 0 else "—"
        top_amp_cnt = filtered_df['อำเภอ_norm'].value_counts().iloc[0] if count_filtered > 0 else 0
        st.metric(
            label="อำเภอที่พบจุดสูงสุด",
            value=f"{top_amp}",
            delta=f"{top_amp_cnt:,} จุด"
        )
        st.metric(
            label="พื้นที่ป่าอนุรักษ์ที่ได้รับผลกระทบ",
            value=f"{filtered_df['ชื่อพื้นที่'].nunique():,} แห่ง"
        )

    with kpi_col4:
        top_station = filtered_df['สถานีฯที่รับผิดชอบ'].value_counts().index[0] if count_filtered > 0 else "—"
        top_station_cnt = filtered_df['สถานีฯที่รับผิดชอบ'].value_counts().iloc[0] if count_filtered > 0 else 0
        st.metric(
            label="สถานีฯ ที่รับภาระงานสูงสุด",
            value=f"{top_station}",
            delta=f"{top_station_cnt:,} จุด"
        )
        st.metric(
            label="ยอดรวมจุดความร้อนทั้งหมด",
            value=f"{total_expected:,} จุด"
        )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Main Visuals: Left Temporal / Right Map
    col_left, col_right = st.columns([1, 1.3])

    with col_left:
        st.markdown("#### แนวโน้มเชิงเวลา (Temporal Trends)")

        # Monthly seasonal wave
        month_order = [
            'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม',
            'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
        ]
        month_counts = filtered_df.groupby(['month_name', 'พ.ศ.'], as_index=False).size()
        month_counts['month_name'] = pd.Categorical(month_counts['month_name'], categories=month_order, ordered=True)
        month_counts = month_counts.sort_values('month_name')

        fig_wave = px.line(
            month_counts,
            x='month_name',
            y='size',
            color='พ.ศ.',
            line_shape='spline',
            markers=True,
            title="การกระจายตัวของจุดความร้อนรายเดือน (Seasonal Wave)",
            labels={'month_name': 'เดือน', 'size': 'จำนวนจุดความร้อน (จุด)', 'พ.ศ.': 'ปี พ.ศ.'},
            color_discrete_sequence=[COLOR_FIRE_PRIMARY, COLOR_FIRE_ACCENT, COLOR_FIRE_LIGHT],
            template="plotly_dark"
        )
        fig_wave.update_layout(
            margin=dict(l=10, r=10, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_wave, use_container_width=True, config=PLOTLY_CONFIG)

        # Hourly Distribution
        hour_df = filtered_df.groupby('hour_of_day', as_index=False).size()
        all_hours = pd.DataFrame({'hour_of_day': list(range(24))})
        hour_df = pd.merge(all_hours, hour_df, on='hour_of_day', how='left').fillna(0)

        fig_hour = px.bar(
            hour_df,
            x='hour_of_day',
            y='size',
            title="การตรวจพบจุดความร้อนรายชั่วโมง (รอบโคจรดาวเทียม)",
            labels={'hour_of_day': 'ชั่วโมง (0-23 น.)', 'size': 'จำนวนจุด'},
            color='size',
            color_continuous_scale="Reds",
            template="plotly_dark"
        )
        fig_hour.update_layout(
            margin=dict(l=10, r=10, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
            xaxis=dict(tickmode='linear', tick0=0, dtick=2)
        )
        st.plotly_chart(fig_hour, use_container_width=True, config=PLOTLY_CONFIG)

        # Forest Type & Confidence Donut charts
        col_donut, col_conf = st.columns(2)
        with col_donut:
            forest_counts = filtered_df['ประเภทป่าอนุรักษ์'].value_counts().reset_index()
            fig_donut = px.pie(
                forest_counts,
                names='ประเภทป่าอนุรักษ์',
                values='count',
                hole=0.55,
                title="สัดส่วนประเภทป่าอนุรักษ์",
                color_discrete_sequence=PLOTLY_FIRE_SEQUENCE,
                template="plotly_dark"
            )
            fig_donut.update_layout(
                margin=dict(l=5, r=5, t=35, b=5),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_donut, use_container_width=True, config=PLOTLY_CONFIG)

        with col_conf:
            conf_counts = filtered_df['CONFEDENCE'].value_counts().reset_index()
            fig_conf = px.pie(
                conf_counts,
                names='CONFEDENCE',
                values='count',
                hole=0.55,
                title="ระดับ CONFEDENCE",
                color_discrete_sequence=['#E53935', '#FB8C00', '#FDD835', '#757575'],
                template="plotly_dark"
            )
            fig_conf.update_layout(
                margin=dict(l=5, r=5, t=35, b=5),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_conf, use_container_width=True, config=PLOTLY_CONFIG)

    with col_right:
        col_m1, col_m2 = st.columns([1.5, 1])
        with col_m1:
            st.markdown("#### แผนที่พิกัดจุดความร้อน (Geographic Map)")
        with col_m2:
            map_type = st.radio(
                "รูปแบบแผนที่",
                options=["จุดพิกัด (Scatter)", "ความหนาแน่น (Density)"],
                horizontal=True,
                label_visibility="collapsed"
            )

        if count_filtered > 0:
            if map_type == "ความหนาแน่น (Density)":
                fig_map = px.density_map(
                    filtered_df,
                    lat='LAT',
                    lon='LONG',
                    radius=12,
                    zoom=7.8,
                    center=dict(lat=14.5, lon=98.8),
                    hover_name='ชื่อพื้นที่',
                    hover_data={
                        'อำเภอ_norm': True,
                        'ตำบล_norm': True,
                        'LAT': ':.4f',
                        'LONG': ':.4f'
                    },
                    map_style="carto-darkmatter",
                    color_continuous_scale="Inferno",
                    title=f"ความหนาแน่นของจุดความร้อน ({count_filtered:,} จุด)",
                    template="plotly_dark"
                )
            else:
                # Dark basemap Map Scatter
                fig_map = px.scatter_map(
                    filtered_df,
                    lat='LAT',
                    lon='LONG',
                    color='ประเภทป่าอนุรักษ์',
                    size_max=8,
                    zoom=7.8,
                    center=dict(lat=14.5, lon=98.8),
                    hover_name='ชื่อพื้นที่',
                    hover_data={
                        'อำเภอ_norm': True,
                        'ตำบล_norm': True,
                        'ว/ด/ป': True,
                        'time_hhmm': True,
                        'CONFEDENCE': True,
                        'LAT': ':.4f',
                        'LONG': ':.4f'
                    },
                    map_style="carto-darkmatter",
                    color_discrete_sequence=PLOTLY_FIRE_SEQUENCE,
                    title=f"การกระจุกตัวของจุดความร้อน ({count_filtered:,} จุด)",
                    template="plotly_dark"
                )

            fig_map.update_layout(
                map_style="carto-darkmatter",
                height=520,
                margin=dict(l=5, r=5, t=35, b=5),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
            )
            st.plotly_chart(fig_map, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.warning("ไม่มีข้อมูลจุดความร้อนตามเงื่อนไขตัวกรองที่เลือก")

        # Treemap Breakdown
        st.markdown("#### โครงสร้างพื้นที่ป่าอนุรักษ์ที่เกิดไฟป่า (Treemap Hierarchy)")
        tree_df = filtered_df.groupby(['อำเภอ_norm', 'ชื่อพื้นที่'], as_index=False).size()
        fig_tree = px.treemap(
            tree_df,
            path=['อำเภอ_norm', 'ชื่อพื้นที่'],
            values='size',
            color='size',
            color_continuous_scale='YlOrRd',
            title="สัดส่วนจุดความร้อนจำแนกตามอำเภอและพื้นที่ป่า",
            template="plotly_dark"
        )
        fig_tree.update_layout(
            height=300,
            margin=dict(l=5, r=5, t=35, b=5),
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_tree, use_container_width=True, config=PLOTLY_CONFIG)

    # Station Workload Section
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("#### ภาระงานสถานีควบคุมไฟป่า (Station Workload)")

    col_st1, col_st2 = st.columns([1.2, 1])

    with col_st1:
        st_work = filtered_df.groupby('สถานีฯที่รับผิดชอบ', as_index=False).agg(
            total_hotspots=('LAT', 'count')
        ).sort_values('total_hotspots', ascending=True)

        fig_st = px.bar(
            st_work,
            x='total_hotspots',
            y='สถานีฯที่รับผิดชอบ',
            orientation='h',
            title="ปริมาณจุดความร้อนในความรับผิดชอบของแต่ละสถานี",
            labels={'total_hotspots': 'จำนวนจุดความร้อน (จุด)', 'สถานีฯที่รับผิดชอบ': 'สถานีควบคุมไฟป่า'},
            color='total_hotspots',
            color_continuous_scale="Reds",
            template="plotly_dark"
        )
        fig_st.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=35, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_st, use_container_width=True, config=PLOTLY_CONFIG)

    with col_st2:
        st.markdown("**ตารางสรุปภาระงานและความน่าเชื่อถือ (Confidence Matrix):**")
        table_st = filtered_df.groupby(['สถานีฯที่รับผิดชอบ', 'CONFEDENCE']).size().unstack(fill_value=0)
        table_st['รวม'] = table_st.sum(axis=1)
        table_st = table_st.sort_values('รวม', ascending=False)
        st.dataframe(
            table_st,
            use_container_width=True,
            height=360
        )
