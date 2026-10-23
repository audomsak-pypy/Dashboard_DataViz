"""
Reusable UI Components: Gauges, KPI Cards, Disclaimers, and Chart Builders.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.config import (
    COLOR_FIRE_ORANGE,
    COLOR_FIRE_RED,
    COLOR_DURIAN_GREEN,
    COLOR_DURIAN_YELLOW,
    COLOR_FOREST_DARK,
    COLOR_ACCENT_BLUE,
    BRD_CAUSAL_DISCLAIMER,
    MAP_CRS_DISCLAIMER,
    ZERO_MISSING_EXPLANATION
)


def render_disclaimer_banner(kind="all"):
    """Renders prominent caution alerts on the Streamlit interface."""
    if kind in ("all", "causal"):
        st.warning(BRD_CAUSAL_DISCLAIMER)
    if kind in ("all", "crs"):
        st.info(MAP_CRS_DISCLAIMER)
    if kind in ("all", "zero_missing"):
        with st.expander("ℹ️ รายละเอียดคำจำกัดความข้อมูล (Zero vs Missing)", expanded=False):
            st.markdown(ZERO_MISSING_EXPLANATION)


def create_gauge_meter(value, max_val, title, unit="", color=COLOR_FIRE_ORANGE):
    """
    Creates an aesthetic semi-circular gauge chart matching the wireframe design.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 14, 'color': '#333'}},
        number={'suffix': f" {unit}", 'font': {'size': 20, 'weight': 'bold'}},
        gauge={
            'axis': {'range': [0, max(max_val, value * 1.1 or 10)], 'tickwidth': 1, 'tickcolor': "#888"},
            'bar': {'color': color},
            'bgcolor': "#EEEEEE",
            'borderwidth': 1,
            'bordercolor': "#CCCCCC",
            'steps': [
                {'range': [0, max_val * 0.5], 'color': '#FFF3E0'},
                {'range': [max_val * 0.5, max_val], 'color': '#FFE0B2'}
            ]
        }
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=15, r=15, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_sparkline_svg(values, width=120, height=30, color="#FF5722"):
    """
    Generates a tiny lightweight SVG sparkline for table cells.
    """
    if not values or len(values) < 2:
        return "—"
    min_v, max_v = min(values), max(values)
    span = max_v - min_v if max_v != min_v else 1.0
    pts = []
    step = width / (len(values) - 1)
    for i, v in enumerate(values):
        x = i * step
        y = height - ((v - min_v) / span * (height - 6) + 3)
        pts.append(f"{x:.1f},{y:.1f}")
    polyline_pts = " ".join(pts)
    return (
        f'<svg width="{width}" height="{height}" style="vertical-align:middle;">'
        f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{polyline_pts}" />'
        f'</svg>'
    )
