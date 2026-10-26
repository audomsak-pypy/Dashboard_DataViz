"""
Kanchanaburi Wildfire & Durian Observatory Dashboard
Refined Single-Page Interactive Layout inspired by Global Forest Fire Dashboard (image.png)
Global cross-filtering across maps, charts, and tables.
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
from dash import dcc, html, Input, Output, State, ctx
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
assert len(df_events_all) == EXPECTED_TOTAL_HOTSPOTS
assert df_joined_all["hotspot_count"].sum() == EXPECTED_TOTAL_HOTSPOTS

amphoe_opts = sorted(df_events_all["อำเภอ_norm"].dropna().unique().tolist())
tambon_opts = sorted(df_events_all["ตำบล_norm"].dropna().unique().tolist())
pa_opts     = sorted(df_events_all["ประเภทป่าอนุรักษ์"].dropna().unique().tolist())
conf_opts   = sorted(df_events_all["CONFEDENCE"].dropna().unique().tolist())

year_ce_min = int(df_events_all["date_parsed"].dt.year.min())
year_ce_max = int(df_events_all["date_parsed"].dt.year.max())
YEAR_FILTER_ALL = "all"
year_ce_values = sorted(int(year) for year in df_events_all["date_parsed"].dt.year.unique())


def resolve_year_range(year_value):
    """Convert the year RangeSlider value into an inclusive [start, end] CE range.

    Accepts:
    - None / YEAR_FILTER_ALL     -> full range
    - [start, end] list/tuple    -> that exact range (RangeSlider output)
    - a single int/str           -> single-year range (legacy fallback)
    """
    if year_value in (None, YEAR_FILTER_ALL):
        return [year_ce_min, year_ce_max]
    if isinstance(year_value, (list, tuple)) and len(year_value) == 2:
        return [int(year_value[0]), int(year_value[1])]
    year = int(year_value)
    return [year, year]


latest_data_date = df_events_all["date_parsed"].max().strftime("%Y-%m-%d")
reporting_day_count = int(df_events_all["date_parsed"].dt.normalize().nunique())
coordinate_rows = df_events_all.dropna(subset=["LAT", "LONG"])
duplicate_coordinate_count = int(coordinate_rows.duplicated(subset=["LAT", "LONG"]).sum())


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
    if state.get("hour") is not None:
        events = events[events["hour_of_day"] == state["hour"]]
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
    durian_year = year_range[1] + 543
    latest_year_area = joined.loc[
        joined["พ.ศ."] == durian_year, "durian_area_rai"
    ].sum(min_count=1)
    durian_total = None if pd.isna(latest_year_area) else float(latest_year_area)
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
    if state.get("hour") is not None:
        comparison_events = comparison_events[
            comparison_events["hour_of_day"] == state["hour"]
        ]
    if state.get("season"):
        dry_months = {11, 12, 1, 2, 3, 4}
        if state["season"] == "dry":
            comparison_events = comparison_events[comparison_events["month"].isin(dry_months)]
        elif state["season"] == "rainy":
            comparison_events = comparison_events[~comparison_events["month"].isin(dry_months)]

    selected_year = year_range[1]
    current_total = int((comparison_events["date_parsed"].dt.year == selected_year).sum())
    previous_year = selected_year - 1
    previous_total = int((comparison_events["date_parsed"].dt.year == previous_year).sum())
    available_years = set(df_events_all["date_parsed"].dt.year.unique())
    yoy = (
        None
        if previous_year not in available_years or previous_total == 0
        else (current_total - previous_total) / previous_total * 100
    )
    return {
        "events": events,
        "joined": joined,
        "hotspot_total": hotspot_total,
        "durian_total": durian_total,
        "durian_year": durian_year,
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

# ─── Dashboard Layout Helpers ─────────────────────────────────
def chart_card(title, content, wide=False, action=None):
    card_class = "chart-card chart-card-wide" if wide else "chart-card"
    header_children = [html.Span(title)]
    if action is not None:
        header_children.append(action)
    return html.Div([
        html.Div(header_children, className="chart-card-header"),
        dcc.Loading(content, type="circle"),
    ], className=card_class)


def comparison_with_disclaimer(content):
    return html.Div([
        content,
        html.P(CAUSAL_DISCLAIMER, className="section-disclaimer"),
    ])


app.layout = html.Div([
    dcc.Store(
        id="cross-filter-store",
        data={
            "tambon": None,
            "amphoe": None,
            "conf": None,
            "pa": None,
            "month": None,
            "season": None,
            "hour": None,
        }
    ),
    html.Header([
        html.Div([
            html.Div("🌐", className="brand-mark"),
            html.Div([
                html.H1("หอดูดาวไฟป่าและพื้นที่ปลูกทุเรียน จังหวัดกาญจนบุรี", className="brand-title"),
                html.P("ข้อมูลจุดความร้อนและพื้นที่เพาะปลูกระดับตำบล", className="brand-subtitle"),
            ]),
        ], className="brand-block"),
    ], className="dashboard-header"),
    html.Main([
        dbc.Alert([
            html.Strong("⚠️ ข้อจำกัดในการตีความ: "),
            html.Span(CAUSAL_DISCLAIMER),
        ], className="viya-disclaimer"),
        dbc.Alert(id="integrity-warning", color="danger", is_open=False, className="integrity-warning"),
        html.Section([
            html.Div([
                html.Label("อำเภอ", className="filter-label"),
                dcc.Dropdown(
                    id="filter-amphoe",
                    options=[{"label": district, "value": district} for district in amphoe_opts],
                    placeholder="ทุกอำเภอ",
                    className="filter-select",
                ),
            ], className="filter-field"),
            html.Div([
                html.Label("ประเภทป่าอนุรักษ์", className="filter-label"),
                dcc.Dropdown(
                    id="filter-pa",
                    options=[{"label": forest, "value": forest} for forest in pa_opts],
                    placeholder="ทุกประเภท",
                    className="filter-select",
                ),
            ], className="filter-field"),
            html.Div([
                html.Label("ความเชื่อมั่น", className="filter-label"),
                dcc.Dropdown(
                    id="filter-conf",
                    options=[{"label": confidence, "value": confidence} for confidence in conf_opts],
                    placeholder="ทุกระดับ",
                    className="filter-select",
                ),
            ], className="filter-field"),
            html.Div([
                html.Label("ช่วงปี ค.ศ.", className="filter-label"),
                dcc.RangeSlider(
                    id="filter-year",
                    min=year_ce_min,
                    max=year_ce_max,
                    step=1,
                    marks={year: {
                        "label": str(year),
                        "style": {
                            "color": "#F1F5F9",
                            "backgroundColor": "#000000",
                            "padding": "2px 7px",
                            "borderRadius": "4px",
                            "border": "1px solid #334155",
                            "fontSize": "0.8rem",
                            "fontWeight": "600",
                        }
                    } for year in year_ce_values},
                    value=[year_ce_min, year_ce_max],
                    tooltip={"placement": "bottom", "always_visible": True},
                    className="year-range-slider",
                ),
            ], className="filter-field filter-field-wide"),
            html.Div([
                html.Div([
                    html.Span("ตัวกรองที่ใช้:"),
                    html.Span(id="filter-pills-container", className="filter-pills"),
                ], className="filter-actions-status"),
                dbc.Button("ล้างตัวกรอง", id="btn-reset", color="danger", outline=True, size="sm"),
            ], className="filter-actions"),
        ], className="filter-bar"),
        html.Div([
            html.Div([
                html.P("จุดความร้อนในช่วงที่เลือก", className="kpi-label"),
                html.Div(id="kpi-hotspot-value", className="kpi-value"),
                html.P(id="kpi-hotspot-delta", className="kpi-meta"),
            ], className="kpi-card kpi-hotspot"),
            html.Div([
                html.P("พื้นที่ทุเรียนปีล่าสุดที่เลือก", className="kpi-label"),
                html.Div(id="kpi-durian-value", className="kpi-value"),
                html.P(id="kpi-durian-meta", className="kpi-meta"),
            ], className="kpi-card kpi-durian"),
            html.Div([
                html.P("พื้นที่ที่เลือก", className="kpi-label"),
                html.Div(id="kpi-selected-area", className="kpi-value"),
                html.P("ขอบเขตการปกครอง", className="kpi-meta"),
            ], className="kpi-card kpi-area"),
            html.Div([
                html.P("คุณภาพข้อมูลจุดความร้อน", className="kpi-label"),
                html.Div(id="kpi-quality-value", className="kpi-value"),
                html.P(id="kpi-quality-meta", className="kpi-meta"),
            ], className="kpi-card kpi-quality"),
        ], className="kpi-strip"),
        html.Section([
            html.H2("💡 ข้อมูลสำคัญจากตัวกรองปัจจุบัน", className="insight-heading"),
            html.Div(id="key-insights", className="key-insights"),
        ], className="key-insights-wrap"),
        html.Div([
            html.Section([
                html.H2([
                    html.Span("1", className="question-number"),
                    html.Span("จุดความร้อนเกิดขึ้นเมื่อไร? (ตามเดือน/ชั่วโมง)"),
                ], className="question-heading"),
                html.P(id="answer-when", className="section-answer"),
                html.Div([
                    chart_card("ช่วงเวลาที่พบจุดความร้อนมาก", html.Div(id="top-hours-list")),
                    chart_card(
                        "จุดความร้อนรายเดือนแยกปี (คลิกแท่งเพื่อกรองเดือนและปี)",
                        dcc.Graph(id="chart-activity", style={"height": "220px"}),
                    ),
                    chart_card(
                        "จุดความร้อนตามเดือนและชั่วโมง (คลิกช่องเพื่อกรอง)",
                        dcc.Graph(id="chart-hour-month", style={"height": "220px"}),
                    ),
                ], className="when-stack"),
            ], className="question-section section-when main-visuals-left"),
            html.Section([
                html.H2([
                    html.Span("2", className="question-number"),
                    html.Span("จุดความร้อนอยู่ที่ไหน?"),
                ], className="question-heading"),
                html.P(id="answer-where", className="section-answer"),
                chart_card(
                    "แผนที่จุดความร้อน (Scatter / Density)",
                    html.Div([
                        html.P(MAP_CRS_NOTE, className="map-crs-note"),
                        dcc.Graph(
                            id="spatial-map",
                            className="spatial-map-graph",
                            style={"height": "100%", "minHeight": "580px"},
                            config={"displayModeBar": True, "scrollZoom": True},
                        ),
                    ], className="spatial-map-wrap"),
                    action=html.Div([
                        html.Div([
                            html.Span("รูปแบบ"),
                            dcc.RadioItems(
                                id="map-mode",
                                options=[
                                    {"label": "จุด", "value": "scatter"},
                                    {"label": "ความหนาแน่น", "value": "density"},
                                ],
                                value="scatter",
                                inline=True,
                                className="map-basemap-options",
                            ),
                        ], className="map-control-group"),
                        html.Div([
                            html.Span("แผนที่"),
                            dcc.RadioItems(
                                id="map-basemap",
                                options=[
                                    {"label": "ดาวเทียม", "value": "satellite"},
                                    {"label": "มืด", "value": "carto-darkmatter"},
                                    {"label": "สว่าง", "value": "open-street-map"},
                                ],
                                value="open-street-map",
                                inline=True,
                                className="map-basemap-options",
                            ),
                        ], className="map-control-group"),
                    ], className="map-controls"),
                ),
                html.Div([
                    chart_card(
                        "ระดับความเชื่อมั่นของจุดความร้อน",
                        dcc.Graph(id="chart-conf-donut", style={"height": "260px"}),
                    ),
                    chart_card(
                        "สัดส่วนตามฤดูกาล (คลิกส่วนเพื่อกรอง)",
                        dcc.Graph(id="chart-seasonality", style={"height": "260px"}),
                    ),
                ], className="sub-map-row"),
            ], className="question-section section-where main-visuals-right"),
        ], className="main-visuals"),
        html.Section([
            html.H2([
                html.Span("3", className="question-number"),
                html.Span("ภาพรวมเพิ่มเติม"),
            ], className="question-heading"),
            html.P(id="answer-durian", className="section-answer"),
            html.P(id="answer-trends", className="section-answer"),
            html.Div([
                chart_card(
                    "จุดความร้อนแยกตามประเภทป่า",
                    dcc.Graph(id="chart-pa-treemap", style={"height": "300px"}),
                ),
                chart_card(
                    "พื้นที่ปลูกทุเรียนรายปี",
                    dcc.Graph(id="chart-durian-trend", style={"height": "300px"}),
                ),
                chart_card(
                    "จำนวนวันที่ตรวจพบจุดความร้อนแยกตามตำบล",
                    dcc.Graph(id="chart-recurrence", style={"height": "300px"}),
                ),
                chart_card(
                    "จุดความร้อนแยกตามอำเภอและประเภทป่าอนุรักษ์",
                    dcc.Graph(id="chart-district-forest", style={"height": "300px"}),
                ),
            ], className="secondary-visuals grid-2x2"),
        ], className="question-section section-more"),
        html.Footer([
            html.Div(id="dynamic-context-card", className="spatial-facts-footer"),
            html.Div([
                html.Span(f"อัปเดตข้อมูลล่าสุด: {latest_data_date}"),
                html.Span(f"จำนวนวันที่มีรายงานการตรวจพบ: {reporting_day_count:,} วัน"),
                html.Span(f"พิกัดซ้ำซ้อน: {duplicate_coordinate_count:,} จุด"),
            ], className="reliability-footer"),
        ], className="page-footer"),
    ], className="dashboard-shell"),
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
    Input("chart-conf-donut", "clickData"),
    Input("chart-pa-treemap", "clickData"),
    Input("chart-activity", "clickData"),
    Input("chart-hour-month", "clickData"),
    Input("chart-seasonality", "clickData"),
    Input("chart-recurrence", "clickData"),
    Input("chart-district-forest", "clickData"),
    Input("filter-amphoe", "value"),
    Input("filter-pa", "value"),
    Input("filter-conf", "value"),
    State("cross-filter-store", "data"),
    prevent_initial_call=True,
)
def handle_all_cross_filters(n_reset, map_click, conf_click, pa_click, act_click,
                             hour_month_click, season_click,
                             recurrence_click, district_forest_click,
                             amphoe_dd, pa_dd, conf_dd, current_store):
    trigger = ctx.triggered_id
    state = dict(current_store) if current_store else {
        "tambon": None, "amphoe": None, "conf": None, "pa": None,
        "month": None, "season": None, "hour": None,
    }

    # 1. Reset Button Clicked
    if trigger == "btn-reset":
        return {
            "tambon": None, "amphoe": None, "conf": None, "pa": None,
            "month": None, "season": None, "hour": None,
        }, None, None, None

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
            rev_map = {v: k for k, v in MONTH_LABELS.items()}
            m_val = rev_map.get(m_label)
            if m_val:
                state["month"] = None if state.get("month") == m_val else m_val
                state["hour"] = None
                state["season"] = None
        except Exception:
            pass

    # 6. Month/hour heatmap clicked
    if trigger == "chart-hour-month" and hour_month_click:
        point = (hour_month_click.get("points") or [None])[0]
        if point:
            month = {label: value for value, label in MONTH_LABELS.items()}.get(
                point.get("y")
            )
            hour = point.get("x")
            if month and isinstance(hour, (int, float)):
                state["month"] = month
                state["hour"] = int(hour)
                state["season"] = None

    # 7. Seasonality chart clicked
    if trigger == "chart-seasonality" and season_click:
        try:
            label = season_click["points"][0].get("x") or season_click["points"][0].get("label")
            season = {"ฤดูแล้ง (พ.ย.–เม.ย.)": "dry", "ฤดูฝน (พ.ค.–ต.ค.)": "rainy"}.get(label)
            if season:
                state["season"] = None if state.get("season") == season else season
                state["month"] = None
                state["hour"] = None
        except Exception:
            pass

    # 8. Recurrence chart click → filter tambon
    if trigger == "chart-recurrence" and recurrence_click:
        point = (recurrence_click.get("points") or [None])[0]
        custom_data = point.get("customdata") if point else None
        if custom_data and len(custom_data) >= 2:
            state["amphoe"], state["tambon"] = custom_data[0], custom_data[1]

    # 9. District and forest type stacked bar
    if trigger == "chart-district-forest" and district_forest_click:
        point = (district_forest_click.get("points") or [None])[0]
        custom_data = point.get("customdata") if point else None
        if custom_data and len(custom_data) >= 2:
            state["amphoe"], state["pa"] = custom_data[0], custom_data[1]
            state["tambon"] = None

    # 10. Dropdown inputs
    if trigger == "filter-amphoe":
        state["amphoe"] = amphoe_dd
    if trigger == "filter-pa":
        state["pa"] = pa_dd
    if trigger == "filter-conf":
        state["conf"] = conf_dd

    return state, state.get("amphoe"), state.get("pa"), state.get("conf")


@app.callback(
    Output("filter-year", "value"),
    Input("chart-activity", "clickData"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def sync_year_controls(activity_click, n_reset):
    """Clicking an activity bar narrows the slider to just that year; Reset restores full range."""
    if ctx.triggered_id == "btn-reset":
        return [year_ce_min, year_ce_max]

    click_data = activity_click
    points = (click_data or {}).get("points") or []
    point = points[0] if points else {}
    custom_data = point.get("customdata") or []
    clicked_year = custom_data[0] if custom_data else None
    selected_year = int(clicked_year) if isinstance(
        clicked_year, (int, float, np.integer, np.floating)
    ) else None
    if selected_year is not None and year_ce_min <= selected_year <= year_ce_max:
        return [selected_year, selected_year]
    return dash.no_update


# ─── Active Filter Pills Renderer ──────────────────────────────
@app.callback(
    Output("filter-pills-container", "children"),
    Input("cross-filter-store", "data"),
    Input("filter-year", "value"),
)
def render_filter_pills(store, year_value):
    if not store:
        return html.Span("แสดงผลภาพรวมทั้งจังหวัด (ไม่มีตัวกรองเฉพาะ)", style={"color": "#64748B", "fontSize": "0.76rem"})

    pills = []
    if year_value not in (None, YEAR_FILTER_ALL):
        if isinstance(year_value, (list, tuple)) and len(year_value) == 2:
            yr_start, yr_end = int(year_value[0]), int(year_value[1])
            if yr_start == yr_end:
                yr_label = str(yr_start)
            else:
                yr_label = f"{yr_start}–{yr_end}"
        else:
            yr_label = str(int(year_value))
        # Only show pill if not full range
        if year_value != [year_ce_min, year_ce_max]:
            pills.append(html.Span(["📅 ปี ค.ศ.: ", html.Strong(yr_label)], className="filter-pill filter-pill-year"))
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
    if store.get("hour") is not None:
        pills.append(html.Span([
            "🕒 ชั่วโมง: ", html.Strong(f"{int(store['hour']):02d}:00–{int(store['hour']):02d}:59")
        ], className="filter-pill"))
    if store.get("season"):
        season_name = "ฤดูแล้ง" if store["season"] == "dry" else "ฤดูฝน"
        pills.append(html.Span(["🌦️ ฤดูกาล: ", html.Strong(season_name)], className="filter-pill"))

    if not pills:
        return html.Span("แสดงผลภาพรวมทั้งจังหวัด (ไม่มีตัวกรองเฉพาะ)", style={"color": "#64748B", "fontSize": "0.76rem"})
    return pills


# ─── Master Unified Visualizations Callback ────────────────────
@app.callback(
    Output("integrity-warning",       "children"),
    Output("integrity-warning",       "is_open"),
    Output("kpi-hotspot-value",       "children"),
    Output("kpi-hotspot-delta",       "children"),
    Output("kpi-durian-value",        "children"),
    Output("kpi-durian-meta",         "children"),
    Output("kpi-selected-area",       "children"),
    Output("kpi-quality-value",       "children"),
    Output("kpi-quality-meta",        "children"),
    Output("key-insights",            "children"),
    Output("answer-when",             "children"),
    Output("answer-where",            "children"),
    Output("answer-durian",           "children"),
    Output("answer-trends",           "children"),
    Output("top-hours-list",          "children"),
    Output("chart-activity",          "figure"),
    Output("chart-hour-month",        "figure"),
    Output("chart-seasonality",       "figure"),
    Output("chart-conf-donut",        "figure"),
    Output("chart-pa-treemap",        "figure"),
    Output("chart-recurrence",        "figure"),
    Output("chart-district-forest",   "figure"),
    Output("dynamic-context-card",    "children"),
    Output("spatial-map",             "figure"),
    Output("chart-durian-trend",      "figure"),
    # Inputs
    Input("cross-filter-store",       "data"),
    Input("filter-year",              "value"),
    Input("map-basemap",              "value"),
    Input("map-mode",                 "value"),
)
def update_entire_dashboard(filter_state, year_value, map_basemap, map_mode):
    state = filter_state or {}
    year_range = resolve_year_range(year_value)
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
            font=dict(color="#E2E8F0", family="Sarabun, Inter", size=12),
            margin=m if m is not None else dict(l=25, r=15, t=25, b=25),
        )
        d.update(kwargs)
        return d

    def empty_chart(message, m=None):
        figure = go.Figure()
        figure.add_annotation(
            text=message,
            showarrow=False,
            font=dict(size=12, color="#94A3B8"),
        )
        figure.update_layout(**get_theme(m=m))
        return figure

    # ── 3. Scorecard values ───────────────────────────────────
    cur_hotspots = metrics["hotspot_total"]

    integrity_warning = None
    integrity_warning_open = False
    is_unfiltered = (
        not any(state.values())
        and year_value in (None, YEAR_FILTER_ALL)
    )
    if is_unfiltered:
        joined_hotspot_total = int(df_joined_all["hotspot_count"].sum())
        if cur_hotspots != len(df_events_all) or cur_hotspots != joined_hotspot_total:
            integrity_warning = (
                "Data integrity mismatch: event, joined-table, and headline "
                f"totals differ ({cur_hotspots:,}, {len(df_events_all):,}, "
                f"{joined_hotspot_total:,})."
            )
            integrity_warning_open = True

    cur_durian_rai = metrics["durian_total"]
    yoy = metrics["yoy"]
    quality_pct = metrics["quality_pct"]
    durian_display = "⬜ Missing" if cur_durian_rai is None else f"{cur_durian_rai:,.1f} ไร่"
    kpi_hotspot_value = f"{cur_hotspots:,} จุด"
    kpi_hotspot_delta = "ไม่มีข้อมูลปีก่อนหน้า" if yoy is None else f"เทียบปีก่อนหน้า: {yoy:+.1f}%"
    kpi_durian_value = durian_display
    kpi_durian_meta = f"พ.ศ. {metrics['durian_year']}"
    if t_filter and a_filter:
        kpi_selected_area = f"ต. {t_filter} · อ. {a_filter}"
    elif t_filter:
        kpi_selected_area = f"ตำบล {t_filter}"
    elif a_filter:
        kpi_selected_area = f"อำเภอ {a_filter}"
    else:
        kpi_selected_area = "จังหวัดกาญจนบุรี"
    kpi_quality_value = f"{quality_pct:.1f}%"
    kpi_quality_meta = f"High/Nominal {metrics['quality_count']:,} จาก {cur_hotspots:,} จุด"

    if df_h.empty:
        answer_when = "ไม่พบข้อมูลจุดความร้อนในช่วงตัวกรองที่เลือก"
        answer_where = answer_when
        empty_insights = [
            answer_when,
            "ไม่สามารถคำนวณเดือนที่พบจุดความร้อนมากที่สุด",
            "ไม่สามารถคำนวณตำบลที่มีจุดความร้อนมากที่สุด",
        ]
        key_insights = [
            html.P([
                html.Span(f"{index:02d}", className="insight-number"),
                html.Span(insight),
            ], className="insight-item")
            for index, insight in enumerate(empty_insights, start=1)
        ]
    else:
        peak_month = int(df_h["month"].value_counts().idxmax())
        peak_month_count = int(df_h["month"].value_counts().max())
        peak_month_share = peak_month_count / len(df_h) * 100
        peak_month_name = MONTH_LABELS[peak_month]
        answer_when = (
            f"เดือน {peak_month_name} มีจุดความร้อนมากที่สุด "
            f"{peak_month_count:,} จุด ({peak_month_share:.1f}%)"
        )
        top_tambon = (
            df_h.groupby(["อำเภอ_norm", "ตำบล_norm"])
            .size()
            .sort_values(ascending=False)
        )
        (top_amphoe, top_tambon_name), top_tambon_count = top_tambon.index[0], int(top_tambon.iloc[0])
        answer_where = (
            f"ตำบล {top_tambon_name} อำเภอ {top_amphoe} มีจุดความร้อน "
            f"มากที่สุด {top_tambon_count:,} จุด"
        )
        peak_hour_counts = df_h["hour_of_day"].value_counts()
        peak_hour = int(peak_hour_counts.idxmax())
        peak_hour_count = int(peak_hour_counts.max())
        peak_hour_share = peak_hour_count / len(df_h) * 100
        key_insights = [
            html.P([
                html.Span("01", className="insight-number"),
                html.Span(f"เดือนสูงสุด: {peak_month_name} ({peak_month_share:.1f}%)"),
            ], className="insight-item"),
            html.P([
                html.Span("02", className="insight-number"),
                html.Span(f"ตำบลที่มีจำนวนสูงสุด: {top_tambon_name} ({top_tambon_count:,} จุด)"),
            ], className="insight-item"),
            html.P([
                html.Span("03", className="insight-number"),
                html.Span(f"ชั่วโมงสูงสุด: {peak_hour:02d}:00–{peak_hour:02d}:59 ({peak_hour_share:.1f}%)"),
            ], className="insight-item"),
        ]
    answer_trends = (
        f"พื้นที่ทุเรียนสำหรับ พ.ศ. {metrics['durian_year']}: {durian_display}"
    )

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
    monthly_events = df_h.assign(year=df_h["date_parsed"].dt.year)
    m_counts = (
        monthly_events.groupby(["year", "month"])
        .size()
        .rename("count")
        .reset_index()
    )
    if not m_counts.empty:
        year_coverage = monthly_events.groupby("year").agg(
            reporting_days=("date_parsed", lambda dates: dates.dt.normalize().nunique()),
            covered_months=("month", "nunique"),
        )
        observed_months = sorted(int(month) for month in m_counts["month"].unique())
        fig_activity = go.Figure()
        for index, year in enumerate(sorted(m_counts["year"].unique())):
            yearly = (
                m_counts[m_counts["year"] == year]
                .set_index("month")
                .reindex(observed_months)
            )
            coverage = year_coverage.loc[year]
            yearly_pct = yearly["count"] / int(yearly["count"].sum()) * 100
            customdata = np.column_stack([
                np.full(len(observed_months), int(year)),
                yearly_pct.to_numpy(),
                np.full(len(observed_months), int(coverage["reporting_days"])),
                np.full(len(observed_months), int(coverage["covered_months"])),
            ])
            fig_activity.add_trace(go.Bar(
                x=[MONTH_LABELS[month] for month in observed_months],
                y=yearly["count"].to_numpy(),
                name=f"พ.ศ. {int(year) + 543}",
                customdata=customdata,
                marker_color=px.colors.qualitative.Safe[index % len(px.colors.qualitative.Safe)],
                hovertemplate=(
                    "พ.ศ. %{customdata[0]:.0f}<br>%{x}: %{y:,.0f} จุด"
                    "<br>สัดส่วนของจุดในปีนั้น: %{customdata[1]:.1f}%"
                    "<br>วันที่มีรายงาน: %{customdata[2]:.0f} วัน"
                    "<br>เดือนที่มีข้อมูล: %{customdata[3]:.0f} เดือน<extra></extra>"
                ),
            ))
        coverage_note = " · ".join(
            f"พ.ศ. {int(year) + 543}: {int(row['covered_months'])} เดือน/"
            f"{int(row['reporting_days'])} วัน"
            for year, row in year_coverage.iterrows()
        )
        fig_activity.update_layout(
            **get_theme(
                m=dict(l=35, r=10, t=55, b=75),
                barmode="group",
                title=dict(
                    text="ข้อมูลที่เลือกครอบคลุม: " + coverage_note,
                    font=dict(size=11, color="#94A3B8"),
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
            )
        )
        fig_activity.update_xaxes(
            categoryorder="array",
            categoryarray=[MONTH_LABELS[month] for month in observed_months],
            gridcolor="#1E293B",
        )
        fig_activity.update_yaxes(gridcolor="#1E293B", title="จุดความร้อนที่ตรวจพบ")
    else:
        fig_activity = empty_chart("ไม่พบข้อมูลรายเดือนในช่วงตัวกรองที่เลือก")

    # ── 6a. Monthly/hourly heatmap ─────────────────────────────
    hour_counts = (
        df_h.groupby(["month", "hour_of_day"])
        .size()
        .rename("count")
        .reset_index()
    )
    if not hour_counts.empty:
        months_with_events = sorted(int(month) for month in hour_counts["month"].unique())
        hour_matrix = (
            hour_counts.pivot(index="month", columns="hour_of_day", values="count")
            .reindex(index=months_with_events, columns=range(24))
            .fillna(0)
        )
        fig_hour_month = go.Figure(go.Heatmap(
            z=hour_matrix.to_numpy(),
            x=list(range(24)),
            y=[MONTH_LABELS[month] for month in months_with_events],
            colorscale="YlOrRd",
            customdata=hour_matrix.to_numpy(),
            colorbar=dict(title="จุด", tickfont=dict(color="#E2E8F0")),
            hovertemplate="%{y} %{x:02d}:00–%{x:02d}:59<br>%{z:,} จุด<extra></extra>",
        ))
        fig_hour_month.update_layout(
            **get_theme(m=dict(l=55, r=20, t=15, b=35))
        )
        fig_hour_month.update_xaxes(
            tickmode="array",
            tickvals=list(range(24)),
            ticktext=[f"{hour:02d}" for hour in range(24)],
            title="ชั่วโมง",
        )
        fig_hour_month.update_yaxes(title="เดือน")
    else:
        fig_hour_month = empty_chart("ไม่พบข้อมูลเดือนและชั่วโมงในช่วงตัวกรองที่เลือก")

    # ── 7. Seasonality indicator ───────────────────────────────
    dry_months = {11, 12, 1, 2, 3, 4}
    season_counts = pd.DataFrame({
        "ฤดูกาล": ["ฤดูแล้ง (พ.ย.–เม.ย.)", "ฤดูฝน (พ.ค.–ต.ค.)"],
        "จำนวน": [int(df_h["month"].isin(dry_months).sum()), int((~df_h["month"].isin(dry_months)).sum())],
    })
    fig_seasonality = px.pie(
        season_counts, names="ฤดูกาล", values="จำนวน", color="ฤดูกาล",
        hole=0.38,
        color_discrete_map={"ฤดูแล้ง (พ.ย.–เม.ย.)": "#F59E0B", "ฤดูฝน (พ.ค.–ต.ค.)": "#38BDF8"},
    )
    fig_seasonality.update_traces(
        texttemplate="%{label}<br>%{value:,} จุด (%{percent})",
        textposition="inside",
        textfont=dict(size=12, color="#0A0E17"),
        hovertemplate="%{label}<br>%{value:,} จุด (%{percent})<extra></extra>",
    )
    fig_seasonality.update_layout(
        **get_theme(m=dict(l=10, r=10, t=10, b=10), showlegend=False)
    )

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
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=12)),
            annotations=[dict(text=f"<b>{center_text}</b><br><span style='font-size:12px'>TOTAL</span>",
                              x=0.5, y=0.5, font_size=16, font_color="#FFFFFF", showarrow=False)]
        )
    )

    # ── 8. Forest Cover Horizontal Bar (Land Cover Breakdown) ─────────
    pa_dist = (
        df_h.groupby("ประเภทป่าอนุรักษ์")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    if len(pa_dist) > 0:
        pa_dist["share_pct"] = pa_dist["count"] / pa_dist["count"].sum() * 100
        fig_treemap = px.bar(
            pa_dist,
            x="count",
            y="ประเภทป่าอนุรักษ์",
            orientation="h",
            text=pa_dist.apply(
                lambda row: f"{row['count']:,} จุด ({row['share_pct']:.1f}%)",
                axis=1,
            ),
            custom_data=["share_pct"],
            color="count",
            color_continuous_scale="Oranges",
        )
        fig_treemap.update_traces(
            textposition="inside",
            textfont=dict(color="#FFFFFF", size=12, family="Sarabun", weight="bold"),
            hovertemplate=(
                "%{y}<br>%{x:,} จุด (%{customdata[0]:.1f}%)<extra></extra>"
            ),
        )
        fig_treemap.update_layout(
            **get_theme(m=dict(l=110, r=10, t=10, b=20), showlegend=False),
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="#1E293B", title=""),
            yaxis=dict(gridcolor="#1E293B", title=""),
        )
    else:
        fig_treemap = go.Figure().update_layout(**get_theme(title="ไม่มีข้อมูล"))

    recurrence_counts = (
        df_h.assign(report_day=df_h["date_parsed"].dt.date)
        .groupby(["อำเภอ_norm", "ตำบล_norm"])["report_day"]
        .nunique()
        .rename("days")
        .reset_index()
    )
    recurrence_top = recurrence_counts.sort_values("days", ascending=True).tail(10).copy()
    recurrence_top["พื้นที่"] = (
        recurrence_top["ตำบล_norm"] + " · " + recurrence_top["อำเภอ_norm"]
    )
    if not recurrence_top.empty:
        fig_recurrence = px.bar(
            recurrence_top,
            x="days",
            y="พื้นที่",
            orientation="h",
            color="days",
            text=recurrence_top["days"].map(lambda days: f"{days:,} วัน"),
            custom_data=["อำเภอ_norm", "ตำบล_norm"],
            color_continuous_scale="Blues",
        )
        fig_recurrence.update_traces(
            textposition="outside",
            textfont=dict(size=12, color="#F8FAFC"),
            hovertemplate="%{y}<br>%{x:,} วัน<extra></extra>",
        )
        fig_recurrence.update_layout(
            **get_theme(
                m=dict(l=150, r=35, t=10, b=20),
                showlegend=False,
                coloraxis_showscale=False,
            )
        )
        fig_recurrence.update_xaxes(gridcolor="#1E293B", title="")
        fig_recurrence.update_yaxes(autorange="reversed", title="")
    else:
        fig_recurrence = empty_chart("ไม่พบวันที่ตรวจพบในช่วงตัวกรองที่เลือก")

    district_forest = (
        df_h.groupby(["อำเภอ_norm", "ประเภทป่าอนุรักษ์"])
        .size()
        .reset_index(name="count")
    )
    if not district_forest.empty:
        fig_district_forest = px.bar(
            district_forest,
            x="อำเภอ_norm",
            y="count",
            color="ประเภทป่าอนุรักษ์",
            barmode="stack",
            custom_data=["อำเภอ_norm", "ประเภทป่าอนุรักษ์"],
            color_discrete_sequence=px.colors.qualitative.Bold,
            labels={"อำเภอ_norm": "อำเภอ", "count": "จุดความร้อน"},
        )
        fig_district_forest.update_traces(
            hovertemplate="%{x}<br>%{fullData.name}: %{y:,} จุด<extra></extra>"
        )
        fig_district_forest.update_layout(
            **get_theme(
                m=dict(l=45, r=15, t=15, b=40),
                barmode="stack",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            )
        )
        fig_district_forest.update_xaxes(gridcolor="#1E293B", title="")
        fig_district_forest.update_yaxes(gridcolor="#1E293B", title="")
    else:
        fig_district_forest = empty_chart("ไม่พบข้อมูลอำเภอในช่วงตัวกรองที่เลือก")

    # ── 9. Section D: Simple Comparison Bar Chart ──────────────
    active_be_years = [y + 543 for y in range(year_range[0], year_range[1] + 1)]
    joined_active = df_joined_all[df_joined_all["พ.ศ."].isin(active_be_years)].copy()
    if a_filter:
        joined_active = joined_active[joined_active["อำเภอ_norm"] == a_filter]
    if t_filter:
        joined_active = joined_active[joined_active["ตำบล_norm"] == t_filter]

    selected_event_counts = (
        df_h.assign(**{"พ.ศ.": df_h["date_parsed"].dt.year + 543})
        .groupby(["อำเภอ_norm", "ตำบล_norm", "พ.ศ."])
        .size()
        .rename("selected_hotspot_count")
        .reset_index()
    )
    joined_active = joined_active.merge(
        selected_event_counts,
        on=["อำเภอ_norm", "ตำบล_norm", "พ.ศ."],
        how="left",
        validate="one_to_one",
    )
    joined_active["hotspot_count"] = (
        joined_active["selected_hotspot_count"].fillna(0).astype(int)
    )

    group_has = joined_active[joined_active["durian_area_rai"] > 0]
    group_no  = joined_active[joined_active["durian_area_rai"] == 0]
    group_missing = joined_active[joined_active["durian_area_rai"].isna()]

    n_has = len(group_has)
    n_no  = len(group_no)
    n_missing = len(group_missing)
    median_has = group_has["hotspot_count"].median() if n_has else 0.0
    median_no = group_no["hotspot_count"].median() if n_no else 0.0
    zero_has = int(group_has["hotspot_count"].eq(0).sum())
    zero_no = int(group_no["hotspot_count"].eq(0).sum())

    if n_has and n_no:
        answer_durian = (
            f"ค่ามัธยฐานจุดความร้อนในระเบียนพื้นที่ทุเรียนมากกว่า 0.0 ไร่ "
            f"คือ {median_has:.1f} จุด (n={n_has:,}); ระเบียน 0.0 ไร่ "
            f"คือ {median_no:.1f} จุด (n={n_no:,})"
        )
    elif n_has:
        answer_durian = f"ระเบียนพื้นที่ทุเรียนมากกว่า 0.0 ไร่มีค่ามัธยฐาน {median_has:.1f} จุด (n={n_has:,})"
    elif n_no:
        answer_durian = f"ระเบียนพื้นที่ทุเรียน 0.0 ไร่มีค่ามัธยฐาน {median_no:.1f} จุด (n={n_no:,})"
    elif n_missing:
        answer_durian = (
            f"พบระเบียนพื้นที่ทุเรียนที่ไม่มีค่า {n_missing:,} ตำบล-ปี "
            "และไม่มีระเบียนพื้นที่ตัวเลขให้เปรียบเทียบ"
        )
    else:
        answer_durian = "ไม่พบระเบียนพื้นที่ทุเรียนในช่วงตัวกรองที่เลือก"

    years_label = (
        f"พ.ศ. {active_be_years[0]}–{active_be_years[-1]}"
        if len(active_be_years) > 1
        else f"พ.ศ. {active_be_years[0]}"
    )
    context_card = html.Div([
        html.P(
            f"❓ ข้อเท็จจริงเชิงพื้นที่ระดับตำบล ({years_label})",
            className="spatial-facts-title",
        ),
        html.P(
            f"กลุ่มพื้นที่ทุเรียนมากกว่า 0.0 ไร่ (n = {n_has} ตำบล-ปี): "
            f"ค่ามัธยฐาน {median_has:.1f} จุด; ไม่พบจุดความร้อน {zero_has:,} ระเบียน",
            className="spatial-facts-line",
        ),
        html.P(
            f"กลุ่มพื้นที่ทุเรียน 0.0 ไร่ (n = {n_no} ตำบล-ปี): "
            f"ค่ามัธยฐาน {median_no:.1f} จุด; ไม่พบจุดความร้อน {zero_no:,} ระเบียน",
            className="spatial-facts-line",
        ),
        html.P(
            f"ระเบียนพื้นที่ทุเรียนที่บันทึกเป็น 0.0 ไร่: {n_no:,} ตำบล-ปี; "
            f"ระเบียนที่ไม่มีค่า (Missing): {n_missing:,} ตำบล-ปี",
            className="spatial-facts-meta",
        ),
        html.P(CAUSAL_DISCLAIMER, className="spatial-facts-disclaimer"),
    ])

    # ── 11. Spatial Map ───────────────────────────────────────
    if cur_hotspots == 0:
        fig_map = empty_chart("ไม่พบจุดความร้อนตามตัวกรองที่เลือก")
        fig_map.update_layout(paper_bgcolor="#0E1624")
    elif map_mode == "density":
        fig_map = px.density_map(
            df_h,
            lat="LAT",
            lon="LONG",
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
            color_continuous_scale="Inferno",
            map_style=map_basemap,
            zoom=8,
            center={"lat": 14.8, "lon": 98.9},
            opacity=0.75,
            radius=20,
        )
        fig_map.update_traces(
            hovertemplate="%{hovertext}<br>ความหนาแน่น: %{z:.2f}<extra></extra>"
        )
        fig_map.update_layout(
            paper_bgcolor="#0E1624",
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(
                title="ความหนาแน่น",
                tickfont=dict(color="#E2E8F0"),
                title_font=dict(color="#E2E8F0"),
            ),
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
                font=dict(size=12, color="#FFFFFF")
            )
        )

    # ── 13. Annual Durian Trend Line ───────────────────────────
    durian_history = df_joined_all.copy()
    if a_filter:
        durian_history = durian_history[durian_history["อำเภอ_norm"] == a_filter]
    if t_filter and a_filter:
        durian_history = durian_history[
            (durian_history["อำเภอ_norm"] == a_filter)
            & (durian_history["ตำบล_norm"] == t_filter)
        ]
    tr_df = (
        durian_history.groupby("พ.ศ.").agg(
            durian_area_rai=("durian_area_rai", lambda values: values.sum(min_count=1)),
            tambon_count=("durian_area_rai", "count"),
        )
        .reset_index()
        .dropna(subset=["durian_area_rai"])
    )
    if not tr_df.empty:
        tr_df["in_selected_year_range"] = tr_df["พ.ศ."].between(
            year_range[0] + 543, year_range[1] + 543
        )
        fig_durian_line = px.line(
            tr_df,
            x="พ.ศ.",
            y="durian_area_rai",
            markers=True,
            text=tr_df["durian_area_rai"].map(lambda area: f"{area:,.0f}"),
            custom_data=["tambon_count", "in_selected_year_range"],
            labels={"พ.ศ.": "พ.ศ.", "durian_area_rai": "พื้นที่ปลูกทุเรียน (ไร่)"},
        )
        fig_durian_line.update_traces(
            line=dict(color="#84CC16", width=2.5),
            marker=dict(
                size=[
                    9 if selected else 6
                    for selected in tr_df["in_selected_year_range"]
                ],
                color=[
                    "#BEF264" if selected else "#64748B"
                    for selected in tr_df["in_selected_year_range"]
                ],
            ),
            textposition="top center",
            textfont=dict(color="#E2E8F0", size=10),
            hovertemplate=(
                "พ.ศ. %{x:.0f}<br>พื้นที่ปลูกทุเรียน: %{y:,.1f} ไร่"
                "<br>ตำบลที่มีข้อมูล: %{customdata[0]:.0f} ตำบล"
                "<br>อยู่ในช่วงปีที่เลือก: %{customdata[1]}<extra></extra>"
            ),
        )
        history_note = (
            "จำนวนตำบลที่มีข้อมูลเปลี่ยนแปลงตามปี; "
            "ยอดรวมระหว่างปีจึงไม่ควรเปรียบเทียบโดยตรง · "
            "จุดสีเขียวแสดงช่วงปีที่เลือก"
        )
        fig_durian_line.update_layout(
            **get_theme(
                m=dict(l=45, r=15, t=20, b=65),
                yaxis_title="พื้นที่ปลูกทุเรียน (ไร่)",
                annotations=[dict(
                    text=history_note,
                    xref="paper", yref="paper",
                    x=0, y=-0.28, showarrow=False,
                    xanchor="left",
                    font=dict(color="#FDE68A", size=11),
                )],
            )
        )
        fig_durian_line.update_xaxes(
            tickmode="array",
            tickvals=tr_df["พ.ศ."].astype(int).tolist(),
            ticktext=tr_df["พ.ศ."].astype(int).astype(str).tolist(),
            gridcolor="#1E293B",
        )
        fig_durian_line.update_yaxes(gridcolor="#1E293B")
    else:
        fig_durian_line = empty_chart("ไม่พบข้อมูลพื้นที่ทุเรียนตามตัวกรองที่เลือก")

    return (
        integrity_warning,
        integrity_warning_open,
        kpi_hotspot_value,
        kpi_hotspot_delta,
        kpi_durian_value,
        kpi_durian_meta,
        kpi_selected_area,
        kpi_quality_value,
        kpi_quality_meta,
        key_insights,
        answer_when,
        answer_where,
        answer_durian,
        answer_trends,
        hours_items,
        fig_activity,
        fig_hour_month,
        fig_seasonality,
        fig_donut,
        fig_treemap,
        fig_recurrence,
        fig_district_forest,
        context_card,
        fig_map,
        fig_durian_line,
    )


# ─── App Runner ────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)
