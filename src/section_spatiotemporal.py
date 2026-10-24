"""
Section 3: Spatial & Temporal Analysis (Split Columns).
Kanchanaburi Wildfire & Durian Spatial Analytics (Ultimate Version).
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.config import (
    COLOR_FIRE_PRIMARY,
    COLOR_FIRE_ACCENT,
    COLOR_FIRE_LIGHT,
    COLOR_FIRE_YELLOW,
    COLOR_MUTED_GRAY,
    COLOR_TEXT_LIGHT,
    PLOTLY_FIRE_SEQUENCE,
    PLOTLY_CONFIG,
    CRS_DISCLAIMER_TEXT
)
from src.components import render_disclaimer_banner


def _fit_view(df: pd.DataFrame, pad: float = 0.15):
    """
    คำนวณจุดกึ่งกลาง (lat, lon) และระดับ zoom ให้พอดีกับขอบเขตพิกัดที่ผ่านการกรอง (Auto-fit Bounding Box)
    """
    if df.empty or 'LAT' not in df.columns or 'LONG' not in df.columns:
        return dict(lat=14.5, lon=98.8), 7.8

    min_lat, max_lat = df['LAT'].min(), df['LAT'].max()
    min_lon, max_lon = df['LONG'].min(), df['LONG'].max()

    if pd.isna(min_lat) or pd.isna(max_lat) or pd.isna(min_lon) or pd.isna(max_lon):
        return dict(lat=14.5, lon=98.8), 7.8

    lat_center = float((min_lat + max_lat) / 2.0)
    lon_center = float((min_lon + max_lon) / 2.0)

    lat_span = float((max_lat - min_lat) * (1.0 + pad))
    lon_span = float((max_lon - min_lon) * (1.0 + pad))

    max_span = max(lat_span, lon_span)
    if max_span <= 0:
        zoom = 11.0
    else:
        zoom = max(min(np.log2(360.0 / max_span) + 0.6, 12.0), 6.5)
        zoom = round(float(zoom), 1)

    return dict(lat=lat_center, lon=lon_center), zoom


def render_spatiotemporal_section(filtered_events: pd.DataFrame):
    """
    Renders Section 1 & 2 in two columns: Left Temporal Analysis, Right Spatial Map.
    """
    count_filtered = len(filtered_events)
    col_left, col_right = st.columns([1, 1.25])

    # ==========================================
    # LEFT COLUMN: 1 จุดความร้อนเกิดขึ้นเมื่อไร? (Temporal)
    # ==========================================
    with col_left:
        # Title and subtext
        st.markdown("<div style='background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #F0F6FC; margin: 0; font-size: 1.05rem;'>1. จุดความร้อนเกิดขึ้นเมื่อไร? (Temporal Trends)</h4>", unsafe_allow_html=True)
        if count_filtered > 0:
            top_month = filtered_events['month_short'].value_counts().index[0]
            top_month_cnt = filtered_events['month_short'].value_counts().iloc[0]
            top_month_pct = (top_month_cnt / count_filtered) * 100
            st.markdown(f"<div style='color: #8B949E; font-size: 0.82rem; margin-top: 4px;'>เดือน <b>{top_month}</b> มีจุดความร้อนมากที่สุด <b>{top_month_cnt:,}</b> จุด ({top_month_pct:.1f}%)</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if count_filtered > 0:
            # Peak hours mini badges (Top 5 windows)
            hour_wins = filtered_events['time_window'].value_counts().head(5).reset_index()
            hour_wins.columns = ['window', 'count']

            st.markdown("<div style='background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 10px 14px; margin-bottom: 14px;'>", unsafe_allow_html=True)
            st.markdown("<div style='font-size: 0.80rem; color: #FF7043; font-weight: 600; margin-bottom: 6px;'>ช่วงเวลาที่พบจุดความร้อนมากที่สุด (Peak Detection Windows)</div>", unsafe_allow_html=True)
            for idx, r in hour_wins.iterrows():
                bar_pct = min(int(r['count'] / hour_wins['count'].max() * 100), 100)
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; font-size: 0.82rem;">
                    <span style="color: #F0F6FC;">{r['window']}</span>
                    <span style="background: #E53935; color: #FFFFFF; font-weight: 600; padding: 1px 8px; border-radius: 4px; font-size: 0.78rem;">{r['count']:,} จุด</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Monthly bar chart grouped by year
            month_order_short = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
            month_grp = filtered_events.groupby(['month_short', 'พ.ศ.'], as_index=False).size()
            month_grp['month_short'] = pd.Categorical(month_grp['month_short'], categories=month_order_short, ordered=True)
            month_grp = month_grp.sort_values('month_short')

            fig_monthly = px.bar(
                month_grp,
                x='month_short',
                y='size',
                color='พ.ศ.',
                barmode='group',
                title="จุดความร้อนรายเดือนแยกปี",
                labels={'month_short': 'เดือน', 'size': 'จำนวนจุด (จุด)', 'พ.ศ.': 'ปี พ.ศ.'},
                color_discrete_sequence=[COLOR_FIRE_PRIMARY, COLOR_FIRE_ACCENT, COLOR_FIRE_LIGHT],
                template="plotly_dark"
            )
            fig_monthly.update_layout(
                height=320,
                margin=dict(l=15, r=15, t=75, b=55),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                title=dict(x=0.02, y=0.96, xanchor='left', yanchor='top'),
                legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5, title_text="")
            )
            st.plotly_chart(fig_monthly, use_container_width=True, config=PLOTLY_CONFIG)

            # Heatmap Month x Hour with Log Scale (np.log1p)
            heat_matrix = filtered_events.groupby(['month_short', 'hour_of_day']).size().unstack(fill_value=0)
            heat_matrix = heat_matrix.reindex(reversed(month_order_short), fill_value=0)
            all_h_cols = list(range(24))
            for h in all_h_cols:
                if h not in heat_matrix.columns:
                    heat_matrix[h] = 0
            heat_matrix = heat_matrix[all_h_cols]

            z_log = np.log1p(heat_matrix.values)
            z_raw = heat_matrix.values

            fig_heat = go.Figure(data=go.Heatmap(
                z=z_log,
                x=[f"{h:02d}" for h in all_h_cols],
                y=list(heat_matrix.index),
                customdata=z_raw,
                hovertemplate="เดือน: %{y}<br>ชั่วโมง: %{x}:00 น.<br>จำนวนจุด: %{customdata:,} จุด<extra></extra>",
                colorscale="YlOrRd",
                colorbar=dict(
                    thickness=10,
                    len=0.8,
                    title=dict(text="log(จุด+1)", font=dict(size=10, color=COLOR_MUTED_GRAY)),
                    tickfont=dict(size=9, color=COLOR_MUTED_GRAY)
                )
            ))
            fig_heat.update_layout(
                height=300,
                margin=dict(l=15, r=15, t=75, b=25),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                title=dict(text="จุดความร้อนตามเดือนและชั่วโมง (00 - 23 น.) [Log Scale]", x=0.02, y=0.96, xanchor='left', yanchor='top'),
                template="plotly_dark"
            )
            st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_CONFIG)
            st.markdown(
                "<div style='color: #8B949E; font-size: 0.78rem; margin-top: -8px; margin-bottom: 16px; line-height: 1.4;'>"
                "หมายเหตุ: จำนวนที่พุ่งสูงในช่วง 13:00-14:00 น. ตรงกับรอบเวลาการผ่านของดาวเทียม (VIIRS/MODIS) ซึ่งเป็นเวลาที่ระบบตรวจพบ ไม่ใช่เวลาที่ไฟเริ่มเกิดจริง"
                "</div>",
                unsafe_allow_html=True
            )

            # Seasonal Proportion Donut
            season_counts = filtered_events['season'].value_counts().reset_index()
            season_counts.columns = ['season', 'count']
            fig_season = px.pie(
                season_counts,
                names='season',
                values='count',
                hole=0.55,
                title="สัดส่วนตามฤดูกาล",
                color='season',
                color_discrete_map={
                    'ฤดูแล้ง (พ.ย.-เม.ย.)': COLOR_FIRE_ACCENT,
                    'ฤดูฝน/อื่นๆ (พ.ค.-ต.ค.)': '#26A69A'
                },
                template="plotly_dark"
            )
            fig_season.update_layout(
                height=260,
                margin=dict(l=15, r=15, t=70, b=35),
                paper_bgcolor="rgba(0,0,0,0)",
                title=dict(x=0.5, y=0.96, xanchor='center', yanchor='top'),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_season, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("ไม่มีข้อมูลจุดความร้อนตามเงื่อนไขตัวกรองที่เลือก")

    # ==========================================
    # RIGHT COLUMN: 2 จุดความร้อนอยู่ที่ไหน? (Spatial)
    # ==========================================
    with col_right:
        # Title and subtext
        st.markdown("<div style='background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #F0F6FC; margin: 0; font-size: 1.05rem;'>2. จุดความร้อนอยู่ที่ไหน? (Spatial Analytics)</h4>", unsafe_allow_html=True)
        if count_filtered > 0:
            top_t = filtered_events['ตำบล_norm'].value_counts().index[0]
            top_a = filtered_events[filtered_events['ตำบล_norm'] == top_t]['อำเภอ_norm'].iloc[0]
            top_cnt = filtered_events['ตำบล_norm'].value_counts().iloc[0]
            st.markdown(f"<div style='color: #8B949E; font-size: 0.82rem; margin-top: 4px;'>ตำบล <b>{top_t}</b> อำเภอ <b>{top_a}</b> มีจุดความร้อน มากที่สุด <b>{top_cnt:,}</b> จุด</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if count_filtered > 0:
            # Map Controls Row
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                map_mode = st.radio(
                    "รูปแบบแผนที่",
                    options=["จุดพิกัด (Scatter)", "ความหนาแน่น (Density)"],
                    horizontal=True,
                    key="map_mode_radio"
                )
            with col_m2:
                map_style_opt = st.radio(
                    "ชั้นแผนที่ฐาน",
                    options=["มืด (Dark)", "ถนน (OSM)"],
                    horizontal=True,
                    key="map_style_radio"
                )

            # Map style selection
            selected_style = "carto-darkmatter" if "มืด" in map_style_opt else "open-street-map"

            render_disclaimer_banner("crs")

            map_center, map_zoom = _fit_view(filtered_events, pad=0.15)

            # Geographic Map Rendering
            if map_mode == "ความหนาแน่น (Density)":
                fig_geo = px.density_map(
                    filtered_events,
                    lat='LAT',
                    lon='LONG',
                    radius=14,
                    zoom=map_zoom,
                    center=map_center,
                    hover_name='ชื่อพื้นที่',
                    hover_data={
                        'อำเภอ_norm': True,
                        'ตำบล_norm': True,
                        'LAT': ':.4f',
                        'LONG': ':.4f'
                    },
                    map_style=selected_style,
                    color_continuous_scale="Inferno",
                    title=f"ความหนาแน่นของจุดความร้อน ({count_filtered:,} จุด)",
                    template="plotly_dark"
                )
            else:
                fig_geo = px.scatter_map(
                    filtered_events,
                    lat='LAT',
                    lon='LONG',
                    color='ประเภทป่าอนุรักษ์',
                    zoom=map_zoom,
                    center=map_center,
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
                    map_style=selected_style,
                    color_discrete_sequence=PLOTLY_FIRE_SEQUENCE,
                    title=f"แผนที่พิกัดจุดความร้อน ({count_filtered:,} จุด)",
                    template="plotly_dark"
                )
                fig_geo.update_traces(
                    marker=dict(size=7, opacity=0.8)
                )

            fig_geo.update_layout(
                height=560,
                margin=dict(l=10, r=10, t=80, b=50),
                paper_bgcolor="rgba(0,0,0,0)",
                title=dict(x=0.02, y=0.96, xanchor='left', yanchor='top'),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.08,
                    xanchor="center",
                    x=0.5,
                    title_text="",
                    font=dict(size=14, color="#F0F6FC"),
                    itemsizing="constant"
                )
            )
            st.plotly_chart(fig_geo, use_container_width=True, config=PLOTLY_CONFIG)

            # Sub-row under map: Confidence Donut + Forest Type Bar Chart
            col_conf, col_forest = st.columns([1, 1.2])

            with col_conf:
                conf_counts = filtered_events['CONFEDENCE'].value_counts().reset_index()
                conf_counts.columns = ['CONFEDENCE', 'count']
                center_text = f"{count_filtered/1000:.1f}K TOTAL" if count_filtered >= 1000 else f"{count_filtered} TOTAL"

                fig_conf = px.pie(
                    conf_counts,
                    names='CONFEDENCE',
                    values='count',
                    hole=0.62,
                    title="ระดับความเชื่อมั่น",
                    color='CONFEDENCE',
                    color_discrete_map={
                        'high': '#E53935',
                        'nominal': '#FB8C00',
                        'low': '#757575',
                        'ไม่ระบุ': '#9E9E9E'
                    },
                    template="plotly_dark"
                )
                fig_conf.update_layout(
                    height=280,
                    margin=dict(l=10, r=10, t=70, b=35),
                    paper_bgcolor="rgba(0,0,0,0)",
                    title=dict(x=0.5, y=0.96, xanchor='center', yanchor='top'),
                    annotations=[dict(text=f"<b>{center_text}</b>", x=0.5, y=0.5, font=dict(size=14, color=COLOR_TEXT_LIGHT), showarrow=False)],
                    legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_conf, use_container_width=True, config=PLOTLY_CONFIG)

            with col_forest:
                all_forest_types = ['เตรียมการเขตห้ามล่าสัตว์ป่า', 'เขตห้ามล่าสัตว์ป่า', 'เขตรักษาพันธุ์สัตว์ป่า', 'อุทยานแห่งชาติ']
                forest_s = filtered_events['ประเภทป่าอนุรักษ์'].value_counts()
                forest_counts = pd.DataFrame({
                    'forest_type': all_forest_types,
                    'count': [int(forest_s.get(ft, 0)) for ft in all_forest_types]
                })
                forest_counts = forest_counts.sort_values('count', ascending=True)
                forest_counts['pct'] = (forest_counts['count'] / count_filtered * 100).round(1) if count_filtered > 0 else 0.0
                forest_counts['label'] = forest_counts.apply(lambda r: f"{r['count']:,} จุด ({r['pct']}%)", axis=1)

                fig_forest = px.bar(
                    forest_counts,
                    x='count',
                    y='forest_type',
                    orientation='h',
                    text='label',
                    title="จุดความร้อนแยกตามประเภทป่า",
                    labels={'count': 'จำนวนจุด', 'forest_type': 'ประเภทป่า'},
                    color='count',
                    color_continuous_scale="Reds",
                    template="plotly_dark"
                )
                fig_forest.update_layout(
                    height=280,
                    margin=dict(l=10, r=25, t=70, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    title=dict(x=0.02, y=0.96, xanchor='left', yanchor='top'),
                    coloraxis_showscale=False
                )
                fig_forest.update_traces(
                    textposition='auto',
                    textfont=dict(color='#FFFFFF', size=11)
                )
                st.plotly_chart(fig_forest, use_container_width=True, config=PLOTLY_CONFIG)

