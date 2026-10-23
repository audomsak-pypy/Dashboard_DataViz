"""
Kanchanaburi Wildfire & Durian Observatory Dashboard
Refined Single-Page Interactive Layout inspired by Global Forest Fire Dashboard (image.png)
Full Two-Way Cross-Filtering across all Maps, Gauges, Treemaps, Donut Slices, and Tables.
"""
import sys
import os
import pandas as pd
import numpy as np

# Plotly & Dash
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
from dash import dcc, html, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc

# Local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    APP_TITLE, COLORS, CAUSAL_DISCLAIMER, MAP_CRS_NOTE,
    MONTH_LABELS, EXPECTED_TOTAL_HOTSPOTS
)
from utils.data_loader import (
    load_hotspot_events, load_joined_table, load_hotspot_agg, get_filter_options
)

# ─── Load Data & Pre-compute Reference Lists ───────────────────
df_events_all = load_hotspot_events()
df_joined_all = load_joined_table()

# Fail early if the stored data is not the validated dashboard dataset.
assert df_joined_all["hotspot_count"].sum() == EXPECTED_TOTAL_HOTSPOTS

amphoe_opts = sorted(df_events_all["อำเภอ_norm"].dropna().unique().tolist())
tambon_opts = sorted(df_events_all["ตำบล_norm"].dropna().unique().tolist())
pa_opts     = sorted(df_events_all["ประเภทป่าอนุรักษ์"].dropna().unique().tolist())
conf_opts   = sorted(df_events_all["CONFEDENCE"].dropna().unique().tolist())

year_ce_min = int(df_events_all["date_parsed"].dt.year.min())
year_ce_max = int(df_events_all["date_parsed"].dt.year.max())


def filter_dashboard_data(filter_state, year_range):
    """Return event and tambon-year data for the active geography and years."""
    state = filter_state or {}
    start_year, end_year = year_range
    events = df_events_all[
        (df_events_all["date_parsed"].dt.year >= start_year)
        & (df_events_all["date_parsed"].dt.year <= end_year)
    ].copy()
    joined = df_joined_all[
        df_joined_all["พ.ศ."].between(start_year + 543, end_year + 543)
    ].copy()

    for column, key in (("อำเภอ_norm", "amphoe"), ("ตำบล_norm", "tambon")):
        if state.get(key):
            events = events[events[column] == state[key]]
            joined = joined[joined[column] == state[key]]
    if state.get("conf"):
        events = events[events["CONFEDENCE"] == state["conf"]]
    if state.get("pa"):
        events = events[events["ประเภทป่าอนุรักษ์"] == state["pa"]]
    if state.get("month"):
        events = events[events["month"] == state["month"]]
    if state.get("season"):
        dry_months = {11, 12, 1, 2, 3, 4}
        if state["season"] == "dry":
            events = events[events["month"].isin(dry_months)]
        elif state["season"] == "rainy":
            events = events[~events["month"].isin(dry_months)]
    return events, joined


def compute_kpis(filter_state, year_range):
    """Single source of truth for all dashboard headline values."""
    events, joined = filter_dashboard_data(filter_state, year_range)
    hotspot_total = int(len(events))
    durian_total = float(joined["durian_area_rai"].sum(min_count=1) or 0)
    quality_count = int(events["CONFEDENCE"].isin(["high", "nominal"]).sum())
    quality_pct = (quality_count / hotspot_total * 100) if hotspot_total else 0.0

    state = filter_state or {}
    comparison_events = df_events_all.copy()
    for column, key in (("อำเภอ_norm", "amphoe"), ("ตำบล_norm", "tambon")):
        if state.get(key):
            comparison_events = comparison_events[comparison_events[column] == state[key]]
    if state.get("conf"):
        comparison_events = comparison_events[comparison_events["CONFEDENCE"] == state["conf"]]
    if state.get("pa"):
        comparison_events = comparison_events[comparison_events["ประเภทป่าอนุรักษ์"] == state["pa"]]
    if state.get("month"):
        comparison_events = comparison_events[comparison_events["month"] == state["month"]]

    selected_year = year_range[1]
    current_total = int((comparison_events["date_parsed"].dt.year == selected_year).sum())
    previous_total = int((comparison_events["date_parsed"].dt.year == selected_year - 1).sum())
    yoy = None if previous_total == 0 else (current_total - previous_total) / previous_total * 100
    return {
        "events": events,
        "joined": joined,
        "hotspot_total": hotspot_total,
        "durian_total": durian_total,
        "quality_count": quality_count,
        "quality_pct": quality_pct,
        "yoy": yoy,
    }

# ─── Dash App Setup ────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700;800&family=Inter:wght@400;600;700;800&display=swap",
    ],
    suppress_callback_exceptions=True,
    title=APP_TITLE,
)

# ─── Custom Dark Aesthetics (Matching image.png) ───────────────
app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
        :root {
            --bg-main: #0A0E17;
            --bg-card: #131B2B;
            --bg-card-header: #0E1624;
            --border-color: #202D42;
            --fire-orange: #EA580C;
            --fire-amber: #F59E0B;
            --fire-glow: rgba(234, 88, 12, 0.25);
            --durian-green: #84CC16;
            --text-main: #F1F5F9;
            --text-muted: #94A3B8;
        }
        body {
            font-family: 'Sarabun', 'Inter', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            margin: 0;
            padding: 0;
        }
        /* Top Navigation Header matching SAS Viya */
        .viya-header {
            background: linear-gradient(90deg, #070B12 0%, #111A29 50%, #070B12 100%);
            border-bottom: 2px solid var(--fire-orange);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
        }
        .viya-title-box {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .viya-globe-icon {
            font-size: 2.2rem;
            color: #F8FAFC;
            background: radial-gradient(circle, #EA580C 20%, transparent 70%);
            border-radius: 50%;
            padding: 2px;
        }
        .viya-title {
            font-size: 1.55rem;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.3px;
            margin: 0;
            line-height: 1.1;
        }
        .viya-subtitle {
            font-size: 0.85rem;
            color: var(--fire-amber);
            font-weight: 600;
            margin: 2px 0 0 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .header-kpi-block {
            display: flex;
            align-items: center;
            gap: 24px;
        }
        .header-kpi-item {
            text-align: right;
            border-left: 1px solid var(--border-color);
            padding-left: 16px;
        }
        .header-kpi-label {
            font-size: 0.72rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0;
        }
        .header-kpi-val {
            font-size: 1.5rem;
            font-weight: 800;
            color: #FFFFFF;
            line-height: 1.2;
            margin: 0;
        }
        /* Card Panels */
        .viya-panel {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
            margin-bottom: 12px;
            overflow: hidden;
        }
        .viya-panel-header {
            background-color: var(--bg-card-header);
            color: #F8FAFC;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 8px 14px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            letter-spacing: 0.2px;
        }
        .viya-panel-body {
            padding: 10px;
        }
        /* Active Filter Badges Bar */
        .filter-status-bar {
            background-color: #0E1624;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 6px 14px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
        }
        .filter-pill {
            background: #1E293B;
            border: 1px solid var(--fire-orange);
            color: #F8FAFC;
            font-size: 0.76rem;
            padding: 3px 10px;
            border-radius: 14px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        /* Most Active Days / Hours list item (inspired by image.png left side) */
        .rank-list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 8px;
            margin-bottom: 4px;
            background-color: #0E1624;
            border-radius: 4px;
            font-size: 0.78rem;
        }
        .rank-list-badge {
            background-color: #D9531E;
            color: #fff;
            padding: 2px 7px;
            border-radius: 3px;
            font-weight: 700;
            font-size: 0.74rem;
        }
        /* Disclaimer Alert */
        .viya-disclaimer {
            background-color: rgba(245, 158, 11, 0.12) !important;
            border: 1px solid rgba(245, 158, 11, 0.35) !important;
            color: #FDE68A !important;
            font-size: 0.78rem !important;
            padding: 7px 14px !important;
            border-radius: 6px !important;
            margin-bottom: 12px !important;
        }
        /* DataTable Dark Overrides */
        .dash-table-container .dash-spreadsheet-container {
            border-radius: 4px;
            overflow: hidden;
        }
        .dash-table-container .dash-spreadsheet-container table {
            font-family: 'Sarabun', sans-serif !important;
            font-size: 0.78rem !important;
        }
        /* RangeSlider Dark Theme styling */
        .rc-slider {
            padding: 12px 0 !important;
        }
        .rc-slider-rail {
            background-color: #202D42 !important;
            height: 6px !important;
        }
        .rc-slider-track {
            background-color: #EA580C !important;
            height: 6px !important;
        }
        .rc-slider-handle {
            border: 2px solid #EA580C !important;
            background-color: #0E1624 !important;
            width: 15px !important;
            height: 15px !important;
            margin-top: -5px !important;
            opacity: 1 !important;
        }
        .rc-slider-handle:hover, .rc-slider-handle:active {
            border-color: #F59E0B !important;
            box-shadow: 0 0 8px rgba(245, 158, 11, 0.6) !important;
        }
        .rc-slider-dot {
            background-color: #202D42 !important;
            border-color: #202D42 !important;
            bottom: -1px !important;
        }
        .rc-slider-dot-active {
            border-color: #EA580C !important;
            background-color: #EA580C !important;
        }
        .rc-slider-mark-text {
            color: #94A3B8 !important;
            font-family: 'Sarabun', sans-serif !important;
            font-size: 0.72rem !important;
            top: 20px !important;
        }
        .rc-slider-mark-text-active {
            color: #F8FAFC !important;
            font-weight: 600 !important;
        }
        .rc-slider-tooltip-inner {
            background-color: #0E1624 !important;
            color: #F8FAFC !important;
            border: 1px solid #EA580C !important;
            font-family: 'Sarabun', sans-serif !important;
            font-size: 0.75rem !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.7) !important;
            border-radius: 4px !important;
            padding: 3px 8px !important;
        }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
'''

# ─── Base Layout ───────────────────────────────────────────────
app.layout = html.Div([

    # Hidden Store: Tracks All Interconnected Active Filters
    dcc.Store(
        id="cross-filter-store",
        data={
            "tambon": None,
            "amphoe": None,
            "conf": None,
            "pa": None,
            "month": None,
            "season": None,
        }
    ),

    # ── Top Navigation Header (Styled like SAS Viya Global Forest Fire) ─
    html.Div([
        # Left Brand
        html.Div([
            html.Div("🌐", className="viya-globe-icon"),
            html.Div([
                html.H1("Kanchanaburi Forest Fire & Durian Observatory", className="viya-title"),
                html.P("ระบบสำรวจจุดความร้อนไฟป่าและพื้นที่เพาะปลูกทุเรียน จังหวัดกาญจนบุรี", className="viya-subtitle"),
            ]),
        ], className="viya-title-box"),

        # Right Header KPIs
        html.Div([
            html.Div([
                html.P("Total Hotspots:", className="header-kpi-label"),
                html.P("—", id="header-hotspot-val", className="header-kpi-val", style={"color": "#EA580C"}),
                html.P("(ตามตัวกรองที่เลือก)", style={"fontSize": "0.68rem", "color": "#94A3B8", "margin": 0}),
            ], className="header-kpi-item"),
            html.Div([
                html.P("Durian Cultivation:", className="header-kpi-label"),
                html.P("—", id="header-durian-val", className="header-kpi-val", style={"color": "#84CC16"}),
                html.P("(ตามตัวกรองที่เลือก)", style={"fontSize": "0.68rem", "color": "#94A3B8", "margin": 0}),
            ], className="header-kpi-item"),
            html.Div([
                html.P("Data Source:", className="header-kpi-label"),
                html.P("สนง.เกษตรฯ / GISTDA", style={"fontSize": "0.95rem", "fontWeight": "700", "color": "#E2E8F0", "margin": 0}),
                html.P("มาตรฐานระบบ GIS กาญจนบุรี", style={"fontSize": "0.68rem", "color": "#94A3B8", "margin": 0}),
            ], className="header-kpi-item"),
        ], className="header-kpi-block"),
    ], className="viya-header"),

    # ── Main Content Container ─────────────────────────────────
    dbc.Container([

        # Disclaimer Alert
        dbc.Alert([
            html.Strong("⚠️ คำเตือนสำคัญด้านการตีความข้อมูล (Disclaimer): "),
            html.Span(CAUSAL_DISCLAIMER),
        ], className="viya-disclaimer mt-2"),

        # ── Global Filter Bar & Interactivity Indicator ────────
        html.Div([
            # Active Pills
            html.Div([
                html.Span("🔍 สถานะตัวกรอง (Interactivity): ", style={"fontSize": "0.78rem", "color": "#94A3B8", "fontWeight": "600"}),
                html.Span(id="filter-pills-container"),
            ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "6px"}),

            # Reset Button & Controls
            html.Div([
                dbc.Button("🔄 ล้างตัวกรองทั้งหมด (Reset All)", id="btn-reset", color="danger", outline=True, size="sm",
                           style={"fontSize": "0.75rem", "padding": "3px 10px", "borderRadius": "14px"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
        ], className="filter-status-bar"),

        # Secondary Filters Drawer
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("📅 ช่วงปี พ.ศ. (ค.ศ.)", style={"fontSize": "0.75rem", "color": "#94A3B8", "fontWeight": "600"}),
                        dcc.RangeSlider(
                            id="filter-year",
                            min=year_ce_min, max=year_ce_max, step=1,
                            value=[year_ce_min, year_ce_max],
                            marks={y: f"{y+543} ({y})" for y in range(year_ce_min, year_ce_max + 1)},
                            tooltip={"placement": "bottom"},
                        ),
                    ], md=4),
                    dbc.Col([
                        html.Label("🏛️ อำเภอ (District)", style={"fontSize": "0.75rem", "color": "#94A3B8", "fontWeight": "600"}),
                        dcc.Dropdown(
                            id="filter-amphoe",
                            options=[{"label": a, "value": a} for a in amphoe_opts],
                            placeholder="ทั้งหมด (หรือคลิกจากกราฟ/แผนที่)",
                            style={"color": "#000"},
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Label("🌲 ประเภทป่าอนุรักษ์ (คลิกจาก Treemap ด้านล่างได้)", style={"fontSize": "0.75rem", "color": "#94A3B8", "fontWeight": "600"}),
                        dcc.Dropdown(
                            id="filter-pa",
                            options=[{"label": p, "value": p} for p in pa_opts],
                            placeholder="ทั้งหมด",
                            style={"color": "#000"},
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Label("📡 CONFEDENCE (คลิกจาก Donut ด้านล่างได้)", style={"fontSize": "0.75rem", "color": "#94A3B8", "fontWeight": "600"}),
                        dcc.Dropdown(
                            id="filter-conf",
                            options=[{"label": c, "value": c} for c in conf_opts],
                            placeholder="ทั้งหมด",
                            style={"color": "#000"},
                        ),
                    ], md=2),
                ], className="align-items-center g-2"),
            ], style={"padding": "8px 14px"}),
        ], className="viya-panel"),

        # ── Phase 9 scorecards ─────────────────────────────────
        dbc.Row([
            dbc.Col(dbc.Card([
                html.Div("จุดความร้อนสะสม", className="viya-panel-header"),
                dbc.CardBody([
                    html.Div(id="kpi-hotspot-value", style={"fontSize": "2.1rem", "fontWeight": "800", "color": "#EA580C"}),
                    html.Div(id="kpi-hotspot-delta", style={"fontSize": "0.78rem", "color": "#94A3B8"}),
                ]),
            ], className="viya-panel h-100"), md=4, className="mb-2"),
            dbc.Col(dbc.Card([
                html.Div("พื้นที่ปลูกทุเรียนในช่วงปีที่เลือก", className="viya-panel-header"),
                dbc.CardBody([
                    html.Div(id="kpi-durian-value", style={"fontSize": "2.1rem", "fontWeight": "800", "color": "#84CC16"}),
                    html.Div(id="kpi-durian-meta", style={"fontSize": "0.78rem", "color": "#94A3B8"}),
                ]),
            ], className="viya-panel h-100"), md=4, className="mb-2"),
            dbc.Col(dbc.Card([
                html.Div("คุณภาพข้อมูลจุดความร้อน", className="viya-panel-header"),
                dbc.CardBody([
                    html.Div(id="kpi-quality-value", style={"fontSize": "2.1rem", "fontWeight": "800", "color": "#38BDF8"}),
                    html.Div(id="kpi-quality-meta", style={"fontSize": "0.78rem", "color": "#94A3B8"}),
                ]),
            ], className="viya-panel h-100"), md=4, className="mb-2"),
        ], className="g-2"),

        # ── MAIN 2-COLUMN COCKPIT GRID ─────────────────────────
        dbc.Row([

            # ═══════════════════════════════════════════════════
            # LEFT COLUMN: Analytics, Gauges & Charts (~58% width)
            # ═══════════════════════════════════════════════════
            dbc.Col([

                # Row 1: Most Active Hours (List) + Fire Activity Trend (Spline Area)
                dbc.Row([
                    # Left: Top Active Hours list (Matching SAS Viya 'Most active days' on left)
                    dbc.Col([
                        dbc.Card([
                            html.Div("🔥 ช่วงเวลาเกิดเหตุสูงสุด", className="viya-panel-header"),
                            dbc.CardBody([
                                html.Div(id="top-hours-list"),
                            ], style={"padding": "8px 10px"}),
                        ], className="viya-panel h-100"),
                    ], md=4, className="mb-2"),

                    # Center: Fire Activity Trend (Bar + Spline Line)
                    dbc.Col([
                        dbc.Card([
                            html.Div([
                                html.Span("📈 ฤดูกาลจุดความร้อนรายเดือน (คลิกข้อมูลเพื่อกรองเดือน)"),
                            ], className="viya-panel-header"),
                            dbc.CardBody([
                                dcc.Graph(id="chart-activity", style={"height": "210px"}),
                            ], className="p-1"),
                        ], className="viya-panel h-100"),
                    ], md=8, className="mb-2"),
                ], className="g-2"),

                # Row 2: Seasonality split
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            html.Div("🌦️ สัดส่วนฤดูแล้งและฤดูฝน (คลิกส่วนเพื่อกรอง)", className="viya-panel-header"),
                            dbc.CardBody([
                                dcc.Graph(id="chart-seasonality", style={"height": "180px"}),
                            ], className="p-1"),
                        ], className="viya-panel h-100"),
                    ], md=12, className="mb-2"),
                ], className="g-2"),

                # Row 3: Confidence Donut + Forest Land Cover Treemap
                dbc.Row([
                    # Confidence Donut (Thick ring with center label, click slice to filter)
                    dbc.Col([
                        dbc.Card([
                            html.Div("📡 ระดับความเชื่อมั่น (คลิกวงแหวน)", className="viya-panel-header"),
                            dbc.CardBody([
                                dcc.Graph(id="chart-conf-donut", style={"height": "190px"}),
                            ], className="p-1"),
                        ], className="viya-panel h-100"),
                    ], md=5, className="mb-2"),

                    # Forest Cover Horizontal Bar (click bar to filter)
                    dbc.Col([
                        dbc.Card([
                            html.Div("🌲 จุดความร้อนแยกประเภทป่า (คลิกแท่งเพื่อกรอง)", className="viya-panel-header"),
                            dbc.CardBody([
                                dcc.Graph(id="chart-pa-treemap", style={"height": "190px"}),
                            ], className="p-1"),
                        ], className="viya-panel h-100"),
                    ], md=7, className="mb-2"),
                ], className="g-2"),

                # Row 4: Section D Simple Comparison + Context Callout Box
                dbc.Row([
                    # Simple Comparison Bar Chart
                    dbc.Col([
                        dbc.Card([
                            html.Div("⚖️ ค่าเฉลี่ยจุดความร้อน: ปลูกทุเรียน vs ไม่ปลูก", className="viya-panel-header"),
                            dbc.CardBody([
                                dcc.Graph(id="chart-simple-comparison", style={"height": "180px"}),
                            ], className="p-1"),
                        ], className="viya-panel h-100"),
                    ], md=6, className="mb-2"),

                    # Dynamic Insight & Context Box (styled like SAS Viya Callout Box with '?' icon)
                    dbc.Col([
                        dbc.Card([
                            html.Div("💡 คำอธิบายเชิงบริบทและข้อเท็จจริง", className="viya-panel-header"),
                            dbc.CardBody([
                                html.Div(id="dynamic-context-card"),
                            ], style={"padding": "10px", "fontSize": "0.78rem", "lineHeight": "1.5"}),
                        ], className="viya-panel h-100"),
                    ], md=6, className="mb-2"),
                ], className="g-2"),

            ], lg=7, md=12),

            # ═══════════════════════════════════════════════════
            # RIGHT COLUMN: Map & Durian Data Table (~42% width)
            # ═══════════════════════════════════════════════════
            dbc.Col([

                # Spatial Map Panel (Satellite / Dark Matter styled like SAS Viya map)
                dbc.Card([
                    html.Div([
                        html.Span("🗺️ แผนที่พิกัดดาวเทียม (คลิกจุดเพื่อเลือกตำบล)"),
                        html.Div([
                            dbc.RadioItems(
                                id="map-basemap",
                                options=[
                                    {"label": " 🛰️ ดาวเทียม", "value": "satellite"},
                                    {"label": " 🌑 มืด", "value": "carto-darkmatter"},
                                    {"label": " 🗺️ ถนน", "value": "open-street-map"},
                                ],
                                value="satellite",
                                inline=True,
                                className="small",
                                style={"fontSize": "0.72rem"}
                            ),
                        ], style={"display": "flex", "gap": "10px"}),
                    ], className="viya-panel-header"),
                    dbc.CardBody([
                        html.P(f"ℹ️ {MAP_CRS_NOTE}", style={"fontSize": "0.7rem", "color": "#F59E0B", "margin": "0 0 4px"}),
                        dcc.Graph(
                            id="spatial-map",
                            style={"height": "460px"},
                            config={"displayModeBar": True, "scrollZoom": True}
                        ),
                    ], className="p-1"),
                ], className="viya-panel mb-2"),

                # Durian Cultivation Ranking Table (like SAS Viya Military Grid table)
                dbc.Card([
                    html.Div([
                        html.Span("🥭 ตารางพื้นที่ปลูกทุเรียนรายตำบล (คลิกแถวเพื่อกรอง)"),
                        html.Span("🟡 = 0.0 ไร่ | ⬜ = Missing", style={"fontSize": "0.7rem", "color": "#94A3B8"}),
                    ], className="viya-panel-header"),
                    dbc.CardBody([
                        html.Div(id="durian-table-container"),
                    ], style={"padding": "8px"}),
                ], className="viya-panel mb-2"),

                # Annual Trend Line Chart for Selected Location
                dbc.Card([
                    html.Div([
                        html.Span("📈 แนวโน้มพื้นที่ปลูกทุเรียนรายปี (พ.ศ. 2561–2568)"),
                    ], className="viya-panel-header"),
                    dbc.CardBody([
                        dcc.Graph(id="chart-durian-trend", style={"height": "165px"}),
                    ], className="p-1"),
                ], className="viya-panel"),

            ], lg=5, md=12),

        ], className="g-2"),

        # Footer
        html.Footer([
            html.P("Kanchanaburi Wildfire & Durian Cultivation Analytics Dashboard | Designed strictly following BRD specifications and Visual Design Guidelines",
                   style={"fontSize": "0.72rem", "color": "#475569", "textAlign": "center", "margin": "16px 0 20px"}),
        ]),

    ], fluid=True, style={"maxWidth": "1720px", "padding": "0 14px"})
])


# ─── Master Cross-Filtering Dispatcher Callback ───────────────
@app.callback(
    Output("cross-filter-store", "data"),
    Output("filter-amphoe", "value"),
    Output("filter-pa", "value"),
    Output("filter-conf", "value"),
    # Inputs
    Input("btn-reset", "n_clicks"),
    Input("spatial-map", "clickData"),
    Input("durian-table-container", "children"), # Table dependency
    Input("chart-conf-donut", "clickData"),
    Input("chart-pa-treemap", "clickData"),
    Input("chart-activity", "clickData"),
    Input("chart-seasonality", "clickData"),
    Input("filter-amphoe", "value"),
    Input("filter-pa", "value"),
    Input("filter-conf", "value"),
    State("cross-filter-store", "data"),
    prevent_initial_call=True,
)
def handle_all_cross_filters(n_reset, map_click, tbl_child, conf_click, pa_click, act_click, season_click,
                             amphoe_dd, pa_dd, conf_dd, current_store):
    trigger = ctx.triggered_id
    state = dict(current_store) if current_store else {"tambon": None, "amphoe": None, "conf": None, "pa": None, "month": None, "season": None}

    # 1. Reset Button Clicked
    if trigger == "btn-reset":
        return {"tambon": None, "amphoe": None, "conf": None, "pa": None, "month": None, "season": None}, None, None, None

    # 2. Map point clicked
    if trigger == "spatial-map" and map_click:
        try:
            pt = map_click["points"][0]
            if "customdata" in pt and pt["customdata"]:
                state["tambon"] = pt["customdata"][0]
                state["amphoe"] = pt["customdata"][1]
        except Exception:
            pass

    # 3. Confidence Donut clicked
    if trigger == "chart-conf-donut" and conf_click:
        try:
            pt = conf_click["points"][0]
            label = pt.get("label")
            state["conf"] = None if state.get("conf") == label else label
        except Exception:
            pass

    # 4. Forest Bar clicked
    if trigger == "chart-pa-treemap" and pa_click:
        try:
            pt = pa_click["points"][0]
            label = pt.get("y") or pt.get("label") or pt.get("id")
            if label in pa_opts:
                state["pa"] = None if state.get("pa") == label else label
        except Exception:
            pass

    # 5. Monthly Activity Bar clicked
    if trigger == "chart-activity" and act_click:
        try:
            pt = act_click["points"][0]
            m_label = pt.get("x")
            # Reverse map label to month int
            rev_map = {v: k for k, v in MONTH_LABELS.items()}
            m_val = rev_map.get(m_label)
            if m_val:
                state["month"] = None if state.get("month") == m_val else m_val
        except Exception:
            pass

    # 6. Seasonality chart clicked
    if trigger == "chart-seasonality" and season_click:
        try:
            label = season_click["points"][0].get("x") or season_click["points"][0].get("label")
            season = {"ฤดูแล้ง (พ.ย.–เม.ย.)": "dry", "ฤดูฝน (พ.ค.–ต.ค.)": "rainy"}.get(label)
            if season:
                state["season"] = None if state.get("season") == season else season
        except Exception:
            pass

    # 7. Dropdown inputs
    if trigger == "filter-amphoe":
        state["amphoe"] = amphoe_dd
    if trigger == "filter-pa":
        state["pa"] = pa_dd
    if trigger == "filter-conf":
        state["conf"] = conf_dd

    return state, state.get("amphoe"), state.get("pa"), state.get("conf")


# ─── Table Row Selection Callback ──────────────────────────────
@app.callback(
    Output("cross-filter-store", "data", allow_duplicate=True),
    Input("durian-datatable", "selected_rows"),
    State("durian-datatable", "data"),
    State("cross-filter-store", "data"),
    prevent_initial_call=True,
)
def handle_table_row_click(selected_rows, table_data, current_store):
    state = dict(current_store) if current_store else {}
    if selected_rows is not None and len(selected_rows) > 0 and table_data:
        idx = selected_rows[0]
        if idx < len(table_data):
            row = table_data[idx]
            state["tambon"] = row.get("ตำบล")
            state["amphoe"] = row.get("อำเภอ")
            return state
    elif selected_rows is not None and len(selected_rows) == 0:
        state["tambon"] = None
        return state
    return dash.no_update


# ─── Active Filter Pills Renderer ──────────────────────────────
@app.callback(
    Output("filter-pills-container", "children"),
    Input("cross-filter-store", "data"),
    Input("filter-year", "value"),
)
def render_filter_pills(store, year_range):
    if not store:
        return html.Span("แสดงผลภาพรวมทั้งจังหวัด (ไม่มีตัวกรองเฉพาะ)", style={"color": "#64748B", "fontSize": "0.76rem"})

    pills = []
    if store.get("tambon"):
        pills.append(html.Span(["📍 ตำบล: ", html.Strong(store["tambon"])], className="filter-pill"))
    if store.get("amphoe") and not store.get("tambon"):
        pills.append(html.Span(["🏛️ อำเภอ: ", html.Strong(store["amphoe"])], className="filter-pill"))
    if store.get("conf"):
        pills.append(html.Span(["📡 ความเชื่อมั่น: ", html.Strong(store["conf"])], className="filter-pill"))
    if store.get("pa"):
        pills.append(html.Span(["🌲 ป่าอนุรักษ์: ", html.Strong(store["pa"])], className="filter-pill"))
    if store.get("month"):
        m_name = MONTH_LABELS.get(store["month"], str(store["month"]))
        pills.append(html.Span(["📅 เดือน: ", html.Strong(m_name)], className="filter-pill"))
    if store.get("season"):
        season_name = "ฤดูแล้ง" if store["season"] == "dry" else "ฤดูฝน"
        pills.append(html.Span(["🌦️ ฤดูกาล: ", html.Strong(season_name)], className="filter-pill"))

    if not pills:
        return html.Span("แสดงผลภาพรวมทั้งจังหวัด (ไม่มีตัวกรองเฉพาะ)", style={"color": "#64748B", "fontSize": "0.76rem"})
    return pills


# ─── Master Unified Visualizations Callback ────────────────────
@app.callback(
    Output("header-hotspot-val",      "children"),
    Output("header-durian-val",       "children"),
    Output("kpi-hotspot-value",       "children"),
    Output("kpi-hotspot-delta",       "children"),
    Output("kpi-durian-value",        "children"),
    Output("kpi-durian-meta",         "children"),
    Output("kpi-quality-value",       "children"),
    Output("kpi-quality-meta",        "children"),
    Output("top-hours-list",          "children"),
    Output("chart-activity",          "figure"),
    Output("chart-seasonality",       "figure"),
    Output("chart-conf-donut",        "figure"),
    Output("chart-pa-treemap",        "figure"),
    Output("chart-simple-comparison", "figure"),
    Output("dynamic-context-card",    "children"),
    Output("spatial-map",             "figure"),
    Output("durian-table-container",  "children"),
    Output("chart-durian-trend",      "figure"),
    # Inputs
    Input("cross-filter-store",       "data"),
    Input("filter-year",              "value"),
    Input("map-basemap",              "value"),
)
def update_entire_dashboard(filter_state, year_range, map_basemap):
    state = filter_state or {}
    t_filter = state.get("tambon")
    a_filter = state.get("amphoe")
    conf_filter = state.get("conf")
    pa_filter = state.get("pa")
    m_filter = state.get("month")

    metrics = compute_kpis(state, year_range)
    df_h = metrics["events"]
    df_d = metrics["joined"]

    # Standardized Layout Theme Helper
    def get_theme(m=None, **kwargs):
        d = dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", family="Sarabun, Inter", size=10),
            margin=m if m is not None else dict(l=25, r=15, t=25, b=25),
        )
        d.update(kwargs)
        return d

    # ── 3. Scorecard values ───────────────────────────────────
    cur_hotspots = metrics["hotspot_total"]

    # Assert the validated total when no cross-filter is active.
    if not t_filter and not a_filter and not conf_filter and not pa_filter and not m_filter and year_range == [year_ce_min, year_ce_max]:
        assert cur_hotspots == EXPECTED_TOTAL_HOTSPOTS, f"Hotspot count mismatch: {cur_hotspots} != {EXPECTED_TOTAL_HOTSPOTS}"

    cur_durian_rai = metrics["durian_total"]
    yoy = metrics["yoy"]
    quality_pct = metrics["quality_pct"]
    # Header and cards use exactly the same calculated values.
    header_hotspot_text = f"{cur_hotspots:,}"
    header_durian_text = f"{cur_durian_rai:,.1f} ไร่"
    kpi_hotspot_value = f"{cur_hotspots:,} จุด"
    kpi_hotspot_delta = "ไม่มีข้อมูลปีก่อนหน้า" if yoy is None else f"เทียบปีก่อนหน้า: {yoy:+.1f}%"
    kpi_durian_value = f"{cur_durian_rai:,.1f} ไร่"
    kpi_durian_meta = f"พ.ศ. {year_range[0] + 543}–{year_range[1] + 543}"
    kpi_quality_value = f"{quality_pct:.1f}%"
    kpi_quality_meta = f"High/Nominal {metrics['quality_count']:,} จาก {cur_hotspots:,} จุด"

    # ── 5. Most Active Hours List (styled like SAS Viya left list) ─
    top_hours = df_h.groupby("hour_of_day").size().reset_index(name="count").sort_values("count", ascending=False).head(5)
    hours_items = []
    for _, r in top_hours.iterrows():
        h = int(r["hour_of_day"])
        c = int(r["count"])
        hours_items.append(
            html.Div([
                html.Span(f"{h:02d}:00 – {h:02d}:59 น.", style={"fontWeight": "600", "color": "#E2E8F0"}),
                html.Span(f"{c:,}", className="rank-list-badge"),
            ], className="rank-list-item")
        )
    if not hours_items:
        hours_items = [html.P("ไม่พบข้อมูลชั่วโมง", style={"fontSize": "0.75rem", "color": "#64748B"})]

    # ── 6. Monthly fire activity by year ───────────────────────
    m_counts = df_h.assign(year=df_h["date_parsed"].dt.year).groupby(["year", "month"]).size().reset_index(name="count")
    fig_activity = go.Figure()
    month_order = list(range(1, 13))
    total_by_month = m_counts.groupby("month")["count"].sum().reindex(month_order, fill_value=0)
    fig_activity.add_trace(go.Bar(
        x=[MONTH_LABELS[m] for m in month_order], y=total_by_month,
        name="รวม", marker=dict(color="#D9531E", opacity=0.36),
        hovertemplate="%{x}<br>รวม %{y:,} จุด<extra></extra>",
    ))
    line_colors = ["#FDE68A", "#38BDF8", "#F87171", "#C4B5FD"]
    for index, year in enumerate(sorted(m_counts["year"].unique())):
        yearly = m_counts[m_counts["year"] == year].set_index("month")["count"].reindex(month_order, fill_value=0)
        fig_activity.add_trace(go.Scatter(
            x=[MONTH_LABELS[m] for m in month_order], y=yearly,
            name=f"พ.ศ. {year + 543}", mode="lines+markers",
            line=dict(color=line_colors[index % len(line_colors)], width=2.2),
            marker=dict(size=5),
            hovertemplate=f"พ.ศ. {year + 543}<br>%{{x}}: %{{y:,}} จุด<extra></extra>",
        ))
    fig_activity.update_layout(
        **get_theme(
            m=dict(l=35, r=10, t=15, b=25),
            barmode="group",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=9)),
        )
    )
    fig_activity.update_xaxes(gridcolor="#1E293B")
    fig_activity.update_yaxes(gridcolor="#1E293B")

    # ── 7. Seasonality indicator ───────────────────────────────
    dry_months = {11, 12, 1, 2, 3, 4}
    season_counts = pd.DataFrame({
        "ฤดูกาล": ["ฤดูแล้ง (พ.ย.–เม.ย.)", "ฤดูฝน (พ.ค.–ต.ค.)"],
        "จำนวน": [int(df_h["month"].isin(dry_months).sum()), int((~df_h["month"].isin(dry_months)).sum())],
    })
    fig_seasonality = px.bar(
        season_counts, x="ฤดูกาล", y="จำนวน", color="ฤดูกาล", text="จำนวน",
        color_discrete_map={"ฤดูแล้ง (พ.ย.–เม.ย.)": "#F59E0B", "ฤดูฝน (พ.ค.–ต.ค.)": "#38BDF8"},
    )
    fig_seasonality.update_traces(texttemplate="%{text:,} จุด", textposition="outside")
    fig_seasonality.update_layout(**get_theme(m=dict(l=35, r=10, t=15, b=30), showlegend=False))
    fig_seasonality.update_xaxes(gridcolor="#1E293B")
    fig_seasonality.update_yaxes(gridcolor="#1E293B")

    # ── 8. Confidence Donut (Thick Donut Ring with Center Text) ──
    conf_dist = df_h["CONFEDENCE"].value_counts().reset_index()
    conf_dist.columns = ["CONFEDENCE", "count"]
    conf_color_map = {"nominal": "#F59E0B", "low": "#38BDF8", "high": "#EF4444"}
    fig_donut = px.pie(
        conf_dist, names="CONFEDENCE", values="count",
        hole=0.68,
        color="CONFEDENCE",
        color_discrete_map=conf_color_map,
    )
    # Center text showing total
    center_text = f"{cur_hotspots/1000:.1f}K" if cur_hotspots >= 1000 else str(cur_hotspots)
    fig_donut.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>จำนวน: %{value:,} จุด (%{percent})<extra></extra>"
    )
    fig_donut.update_layout(
        **get_theme(
            m=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=9)),
            annotations=[dict(text=f"<b>{center_text}</b><br><span style='font-size:9px'>TOTAL</span>",
                              x=0.5, y=0.5, font_size=16, font_color="#FFFFFF", showarrow=False)]
        )
    )

    # ── 8. Forest Cover Horizontal Bar (Land Cover Breakdown) ─────────
    pa_dist = df_h.groupby("ประเภทป่าอนุรักษ์").size().reset_index(name="count").sort_values("count", ascending=True)
    if len(pa_dist) > 0:
        fig_treemap = px.bar(
            pa_dist,
            x="count",
            y="ประเภทป่าอนุรักษ์",
            orientation="h",
            text=pa_dist["count"].apply(lambda v: f"{v:,} จุด"),
            color="count",
            color_continuous_scale="Oranges",
        )
        fig_treemap.update_traces(
            textposition="inside",
            textfont=dict(color="#FFFFFF", size=10, family="Sarabun", weight="bold")
        )
        fig_treemap.update_layout(
            **get_theme(m=dict(l=110, r=10, t=10, b=20), showlegend=False),
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="#1E293B", title=""),
            yaxis=dict(gridcolor="#1E293B", title=""),
        )
    else:
        fig_treemap = go.Figure().update_layout(**get_theme(title="ไม่มีข้อมูล"))

    # ── 9. Section D: Simple Comparison Bar Chart ──────────────
    active_be_years = [y + 543 for y in range(year_range[0], year_range[1] + 1)]
    joined_active = df_joined_all[df_joined_all["พ.ศ."].isin(active_be_years)].copy()
    if a_filter:
        joined_active = joined_active[joined_active["อำเภอ_norm"] == a_filter]
    if t_filter:
        joined_active = joined_active[joined_active["ตำบล_norm"] == t_filter]

    group_has = joined_active[joined_active["durian_area_rai"] > 0]
    group_no  = joined_active[joined_active["durian_area_rai"] == 0]

    n_has = len(group_has)
    n_no  = len(group_no)
    avg_has = group_has["hotspot_count"].mean() if n_has > 0 else 0.0
    avg_no  = group_no["hotspot_count"].mean() if n_no > 0 else 0.0
    sum_has = group_has["hotspot_count"].sum()
    sum_no  = group_no["hotspot_count"].sum()

    comp_df = pd.DataFrame({
        "กลุ่ม": [f"ปลูกทุเรียน (>0 ไร่)<br>(n={n_has})", f"ไม่ปลูก (0 ไร่)<br>(n={n_no})"],
        "ค่าเฉลี่ย": [avg_has, avg_no],
        "จำนวน": [n_has, n_no]
    })
    fig_comp = px.bar(
        comp_df, x="กลุ่ม", y="ค่าเฉลี่ย",
        color="กลุ่ม",
        text=comp_df.apply(lambda r: f"{r['ค่าเฉลี่ย']:.1f} จุด (n={r['จำนวน']})", axis=1),
        color_discrete_sequence=["#84CC16", "#64748B"],
    )
    fig_comp.update_traces(textposition="outside", textfont=dict(size=11, color="#F8FAFC"))
    fig_comp.update_layout(
        **get_theme(
            m=dict(l=30, r=10, t=25, b=30),
            showlegend=False,
        )
    )
    fig_comp.update_yaxes(gridcolor="#1E293B")
    fig_comp.update_xaxes(gridcolor="#1E293B")

    # ── 10. Dynamic Insight Callout Box (styled like SAS Viya '?')
    years_label = f"พ.ศ. {active_be_years[0]}–{active_be_years[-1]}" if len(active_be_years) > 1 else f"พ.ศ. {active_be_years[0]}"
    context_card = html.Div([
        html.Div([
            html.Span("❓", style={"fontSize": "1.3rem", "color": "#F59E0B"}),
            html.Span(f"ข้อเท็จจริงเชิงพื้นที่ระดับตำบล ({years_label})", style={"fontWeight": "700", "color": "#F8FAFC"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "6px", "marginBottom": "6px"}),
        html.P([
            f"• กลุ่มตำบลที่มีการปลูกทุเรียน (n = {n_has} ตำบล-ปี): พบจุดความร้อนเฉลี่ย ",
            html.Strong(f"{avg_has:.1f} จุด/ตำบล ", style={"color": "#EA580C"}),
            f"(ยอดรวม {sum_has:,} จุด)"
        ], style={"margin": "0 0 4px 0"}),
        html.P([
            f"• กลุ่มตำบลที่ไม่มีการปลูกทุเรียน (n = {n_no} ตำบล-ปี): พบจุดความร้อนเฉลี่ย ",
            html.Strong(f"{avg_no:.1f} จุด/ตำบล ", style={"color": "#94A3B8"}),
            f"(ยอดรวม {sum_no:,} จุด)"
        ], style={"margin": "0 0 6px 0"}),
        html.Div([
            html.Small(
                f"🔍 หมายเหตุด้านความสมดุลข้อมูล (Sample Size & Confounder): "
                f"กลุ่มไม่ปลูกมีเพียง {n_no} รายการ เนื่องจากสำนักงานเกษตรจังหวัดรายงานเฉพาะตำบลที่ทำการสำรวจ ส่วนตำบลอื่นๆ ที่ไม่ปรากฏถือเป็นข้อมูล Missing "
                "และจุดความร้อนส่วนใหญ่กระจุกตัวในป่าอนุรักษ์ขนาดใหญ่ที่อยู่ในเขตการปกครองระดับตำบลเดียวกัน "
                "ไม่สามารถสรุปเชิงสาเหตุว่าสวนทุเรียนเป็นต้นเหตุของไฟป่าได้",
                style={"color": "#94A3B8", "lineHeight": "1.4", "display": "block"}
            )
        ], style={"backgroundColor": "#0E1624", "padding": "6px 8px", "borderRadius": "4px", "borderLeft": "3px solid #F59E0B"}),
    ])

    # ── 11. Spatial Map (Satellite / Dark Matter) ───────────────
    if cur_hotspots == 0:
        fig_map = go.Figure().update_layout(
            paper_bgcolor="#0E1624",
            font=dict(color="#E2E8F0", family="Sarabun"),
            title="ไม่พบจุดความร้อนตามตัวกรองที่เลือก"
        )
    else:
        fig_map = px.scatter_map(
            df_h,
            lat="LAT",
            lon="LONG",
            color="ประเภทป่าอนุรักษ์",
            hover_name="ตำบล_norm",
            hover_data={
                "อำเภอ_norm": True,
                "ตำบล_norm": True,
                "ว/ด/ป": True,
                "time_hhmm": True,
                "สถานีฯที่รับผิดชอบ": True,
                "CONFEDENCE": True,
                "LAT": False,
                "LONG": False,
            },
            custom_data=["ตำบล_norm", "อำเภอ_norm"],
            map_style=map_basemap,
            zoom=8,
            center={"lat": 14.8, "lon": 98.9},
            opacity=0.8,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_map.update_traces(marker=dict(size=7))
        fig_map.update_layout(
            paper_bgcolor="#0E1624",
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=0.01,
                xanchor="right", x=0.99,
                bgcolor="rgba(10, 14, 23, 0.85)",
                font=dict(size=9, color="#FFFFFF")
            )
        )

    # ── 12. Durian Cultivation Ranking Table ────────────────────
    tbl_group = df_d.groupby(["อำเภอ_norm", "ตำบล_norm"]).agg(
        avg_rai=("durian_area_rai", "mean"),
        latest_rai=("durian_area_rai", lambda x: x.iloc[-1] if len(x)>0 else np.nan),
        total_hotspots=("hotspot_count", "sum")
    ).reset_index()

    tbl_group = tbl_group.sort_values("latest_rai", ascending=False).reset_index(drop=True)
    tbl_group.insert(0, "อันดับ", tbl_group.index + 1)

    display_rows = []
    selected_idx = []
    for i, row in tbl_group.iterrows():
        t_name = row["ตำบล_norm"]
        lat_val = row["latest_rai"]
        avg_val = row["avg_rai"]
        hot_val = row["total_hotspots"]

        if t_filter and t_name == t_filter:
            selected_idx = [i]

        def fmt_v(v):
            if pd.isna(v):
                return "⬜ Missing"
            elif v == 0.0:
                return "🟡 0.0"
            return f"{v:,.1f}"

        display_rows.append({
            "อันดับ": row["อันดับ"],
            "อำเภอ": row["อำเภอ_norm"],
            "ตำบล": t_name,
            "เฉลี่ย (ไร่)": fmt_v(avg_val),
            "ปี 68 (ไร่)": fmt_v(lat_val),
            "จุดความร้อน": f"{hot_val:,}",
        })

    durian_table = dash_table.DataTable(
        id="durian-datatable",
        data=display_rows,
        columns=[
            {"name": "อันดับ", "id": "อันดับ"},
            {"name": "อำเภอ", "id": "อำเภอ"},
            {"name": "ตำบล", "id": "ตำบล"},
            {"name": "เฉลี่ย (ไร่)", "id": "เฉลี่ย (ไร่)"},
            {"name": "ปี 68 (ไร่)", "id": "ปี 68 (ไร่)"},
            {"name": "จุดความร้อน", "id": "จุดความร้อน"},
        ],
        row_selectable="single",
        selected_rows=selected_idx,
        page_size=6,
        sort_action="native",
        filter_action="native",
        style_header={
            "backgroundColor": "#0E1624",
            "color": "#F8FAFC",
            "fontWeight": "700",
            "border": "1px solid #202D42",
            "fontSize": "0.75rem",
            "height": "28px"
        },
        style_data={
            "backgroundColor": "#131B2B",
            "color": "#E2E8F0",
            "border": "1px solid #202D42",
            "fontSize": "0.75rem",
            "height": "26px",
        },
        style_data_conditional=[
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(234, 88, 12, 0.4)",
                "border": "1px solid #EA580C",
                "fontWeight": "bold",
            },
            {
                "if": {"filter_query": '{ปี 68 (ไร่)} contains "🟡"'},
                "color": "#F59E0B",
                "backgroundColor": "#1A180E",
            },
            {
                "if": {"filter_query": '{ปี 68 (ไร่)} contains "Missing"'},
                "color": "#64748B",
            },
        ],
        style_table={"overflowX": "auto"},
    )

    # ── 13. Annual Durian Trend Line ───────────────────────────
    if t_filter:
        tr_df = df_d[df_d["ตำบล_norm"] == t_filter].groupby("พ.ศ.")["durian_area_rai"].sum(min_count=1).reset_index()
        tr_title = f"พื้นที่ทุเรียน ต.{t_filter} (ไร่)"
    elif a_filter:
        tr_df = df_d[df_d["อำเภอ_norm"] == a_filter].groupby("พ.ศ.")["durian_area_rai"].sum(min_count=1).reset_index()
        tr_title = f"พื้นที่ทุเรียน อ.{a_filter} (ไร่)"
    else:
        tr_df = df_d.groupby("พ.ศ.")["durian_area_rai"].sum(min_count=1).reset_index()
        tr_title = "พื้นที่ทุเรียนทั้งจังหวัดกาญจนบุรี (ไร่)"

    fig_durian_line = px.line(
        tr_df, x="พ.ศ.", y="durian_area_rai",
        markers=True,
        labels={"พ.ศ.": "", "durian_area_rai": ""},
    )
    fig_durian_line.update_traces(
        line=dict(color="#84CC16", width=2.5),
        marker=dict(size=6, color="#BEF264")
    )
    fig_durian_line.update_layout(
        **get_theme(
            m=dict(l=35, r=10, t=25, b=20),
            title=dict(text=tr_title, font=dict(size=10, color="#94A3B8"))
        )
    )
    fig_durian_line.update_xaxes(tickmode="linear", tick0=2561, dtick=1, gridcolor="#1E293B")
    fig_durian_line.update_yaxes(gridcolor="#1E293B")

    return (
        header_hotspot_text,
        header_durian_text,
        kpi_hotspot_value,
        kpi_hotspot_delta,
        kpi_durian_value,
        kpi_durian_meta,
        kpi_quality_value,
        kpi_quality_meta,
        hours_items,
        fig_activity,
        fig_seasonality,
        fig_donut,
        fig_treemap,
        fig_comp,
        context_card,
        fig_map,
        durian_table,
        fig_durian_line
    )


# ─── App Runner ────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)
