"""
Reusable Professional Dark UI Components: Gauges, Donut Indicators, KPI Cards, and Notices.
Kanchanaburi Wildfire & Durian Spatial Analytics (Ultimate Version).
"""

import streamlit as st
import plotly.graph_objects as go
from src.config import (
    COLOR_FIRE_PRIMARY,
    COLOR_FIRE_ACCENT,
    COLOR_FIRE_LIGHT,
    COLOR_FIRE_YELLOW,
    COLOR_CARD_DARK,
    COLOR_BORDER_DARK,
    COLOR_TEXT_LIGHT,
    COLOR_MUTED_GRAY,
    CAUSAL_DISCLAIMER_TEXT,
    CRS_DISCLAIMER_TEXT,
    PLOTLY_CONFIG
)

__all__ = [
    'render_disclaimer_banner',
    'render_kpi_card',
    'render_highlights_strip',
    'create_donut_indicator',
    'create_gauge_meter'
]


def render_disclaimer_banner(kind="causal"):
    """Renders sleek, minimalist academic warning banners without emojis."""
    if kind == "causal":
        st.markdown(
            f"""
            <div style="background-color: #1A1612; border: 1px solid #D97706; border-left: 4px solid #F59E0B; 
                        padding: 10px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 0.86rem; color: #FCD34D;">
                <b>{CAUSAL_DISCLAIMER_TEXT}</b>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif kind == "crs":
        st.markdown(
            f"""
            <div style="color: #FF7043; font-size: 0.80rem; margin-top: 4px; margin-bottom: 8px;">
                {CRS_DISCLAIMER_TEXT}
            </div>
            """,
            unsafe_allow_html=True
        )


def render_kpi_card(title, value, delta=None, delta_val=None, **kwargs):
    """
    ฟังก์ชันสำหรับแสดงผลการ์ด KPI บนแดชบอร์ด
    รองรับ delta_val:
    - delta_val > 0 (จุดความร้อนเพิ่ม = แย่): แสดงสีแดง #E53935 พร้อมลูกศรขึ้น ▲
    - delta_val < 0 (จุดความร้อนลด = ดี): แสดงสีเขียว #2EA043 พร้อมลูกศรลง ▼
    - delta_val == 0 หรือ None (ไม่มีการเปลี่ยนแปลง/ค่าทั่วไป): แสดงสีเทา #8B949E
    """
    if delta is None and 'delta_str' in kwargs:
        delta = kwargs['delta_str']

    delta_text = str(delta) if delta is not None else ""

    if delta_val is not None:
        if delta_val > 0:
            arrow = "▲"
            color = "#E53935"
        elif delta_val < 0:
            arrow = "▼"
            color = "#2EA043"
        else:
            arrow = "—"
            color = "#8B949E"
        delta_html = f'<div style="color: {color}; font-size: 0.82rem; font-weight: 600; margin-top: 4px;">{arrow} {delta_text}</div>'
    elif delta_text:
        delta_html = f'<div style="color: #8B949E; font-size: 0.82rem; font-weight: 500; margin-top: 4px;">{delta_text}</div>'
    else:
        delta_html = '<div style="height: 18px; margin-top: 4px;"></div>'

    html = f"""
    <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 12px 16px; min-height: 96px;">
        <div style="color: #8B949E; font-size: 0.88rem; font-weight: 500; white-space: normal; word-break: break-word; line-height: 1.3;">{title}</div>
        <div style="color: #F0F6FC; font-size: 1.5rem; font-weight: 700; white-space: normal; word-break: break-word; margin-top: 3px;">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_highlights_strip(item1: str, item2: str, item3: str):
    """
    Renders the highlights strip (01, 02, 03) across the top below the KPIs.
    """
    html = f"""
    <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; 
                padding: 10px 16px; margin-top: 14px; margin-bottom: 20px; display: flex; flex-wrap: wrap; 
                align-items: center; justify-content: space-between; gap: 12px; font-size: 0.85rem;">
        <div style="color: #FF7043; font-weight: 600;">ข้อมูลสำคัญจากตัวกรองปัจจุบัน:</div>
        <div style="display: flex; align-items: center;">
            <span style="background: #E53935; color: #FFFFFF; font-size: 0.72rem; font-weight: 700; 
                         padding: 2px 7px; border-radius: 4px; margin-right: 8px;">01</span>
            <span style="color: #F0F6FC;">{item1}</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="background: #FF7043; color: #FFFFFF; font-size: 0.72rem; font-weight: 700; 
                         padding: 2px 7px; border-radius: 4px; margin-right: 8px;">02</span>
            <span style="color: #F0F6FC;">{item2}</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="background: #FFA726; color: #161B22; font-size: 0.72rem; font-weight: 700; 
                         padding: 2px 7px; border-radius: 4px; margin-right: 8px;">03</span>
            <span style="color: #F0F6FC;">{item3}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def create_donut_indicator(value, total, title, center_text, color=COLOR_FIRE_PRIMARY):
    """
    Creates a donut gauge with center text.
    """
    pct = (value / total * 100) if total > 0 else 0
    rem = max(total - value, 0)

    fig = go.Figure(data=[go.Pie(
        values=[value, rem],
        labels=['Active', 'Remaining'],
        hole=0.68,
        marker=dict(colors=[color, '#21262D']),
        textinfo='none',
        hoverinfo='none',
        sort=False
    )])

    fig.update_layout(
        template="plotly_dark",
        height=140,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{center_text}</b>",
                x=0.5, y=0.5,
                font=dict(size=14, color=COLOR_TEXT_LIGHT),
                showarrow=False
            )
        ],
        title=dict(text=title, font=dict(size=12, color=COLOR_MUTED_GRAY), x=0.5, y=0.98, xanchor='center')
    )
    return fig


def create_gauge_meter(value, max_val, title, unit="", color=COLOR_FIRE_PRIMARY):
    """
    Creates an executive dark semi-circular gauge chart.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 12, 'color': COLOR_MUTED_GRAY}},
        number={'suffix': f" {unit}", 'font': {'size': 20, 'color': COLOR_TEXT_LIGHT, 'weight': 'bold'}},
        gauge={
            'axis': {
                'range': [0, max(max_val, value * 1.05 or 10)],
                'tickwidth': 1,
                'tickcolor': COLOR_BORDER_DARK,
                'tickfont': {'color': COLOR_MUTED_GRAY, 'size': 9}
            },
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "#21262D",
            'borderwidth': 1,
            'bordercolor': COLOR_BORDER_DARK
        }
    ))
    fig.update_layout(
        template="plotly_dark",
        height=140,
        margin=dict(l=15, r=15, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig
