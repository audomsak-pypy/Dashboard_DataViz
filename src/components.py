"""
Reusable Professional Dark UI Components: Gauges, KPI Cards, and Notices.
"""

import streamlit as st
import plotly.graph_objects as go
from src.config import (
    COLOR_FIRE_PRIMARY,
    COLOR_FIRE_ACCENT,
    COLOR_CARD_DARK,
    COLOR_BORDER_DARK,
    COLOR_TEXT_LIGHT,
    COLOR_MUTED_GRAY,
    BRD_CAUSAL_DISCLAIMER,
    MAP_CRS_DISCLAIMER,
    ZERO_MISSING_EXPLANATION
)


def render_disclaimer_banner(kind="all"):
    """Renders sleek, minimalist academic disclaimers without emojis."""
    if kind in ("all", "causal"):
        st.markdown(
            f"""
            <div style="background-color: #1A1414; border: 1px solid #7F1D1D; border-left: 4px solid #EF4444; 
                        padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 0.88rem; color: #FCA5A5;">
                {BRD_CAUSAL_DISCLAIMER}
            </div>
            """,
            unsafe_allow_html=True
        )
    if kind in ("all", "crs"):
        st.markdown(
            f"""
            <div style="background-color: #161B22; border: 1px solid #30363D; border-left: 4px solid #FF7043; 
                        padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; font-size: 0.85rem; color: #C9D1D9;">
                {MAP_CRS_DISCLAIMER}
            </div>
            """,
            unsafe_allow_html=True
        )
    if kind in ("all", "zero_missing"):
        st.markdown(
            f"""
            <div style="background-color: #161B22; border: 1px solid #30363D; border-left: 4px solid #FFA726; 
                        padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; font-size: 0.85rem; color: #C9D1D9;">
                {ZERO_MISSING_EXPLANATION}
            </div>
            """,
            unsafe_allow_html=True
        )


def create_gauge_meter(value, max_val, title, unit="", color=COLOR_FIRE_PRIMARY):
    """
    Creates an executive dark semi-circular gauge chart.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 13, 'color': COLOR_MUTED_GRAY, 'family': 'sans-serif'}},
        number={'suffix': f" {unit}", 'font': {'size': 22, 'color': COLOR_TEXT_LIGHT, 'weight': 'bold'}},
        gauge={
            'axis': {
                'range': [0, max(max_val, value * 1.1 or 10)],
                'tickwidth': 1,
                'tickcolor': COLOR_BORDER_DARK,
                'tickfont': {'color': COLOR_MUTED_GRAY, 'size': 10}
            },
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "#21262D",
            'borderwidth': 1,
            'bordercolor': COLOR_BORDER_DARK,
            'steps': [
                {'range': [0, max_val * 0.5], 'color': '#211B1B'},
                {'range': [max_val * 0.5, max_val], 'color': '#381C1C'}
            ]
        }
    ))
    fig.update_layout(
        template="plotly_dark",
        height=170,
        margin=dict(l=15, r=15, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig
