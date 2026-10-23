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
assert len(df_events_all) == EXPECTED_TOTAL_HOTSPOTS
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


def question_section(number, title, answer_id, cards, section_class, disclaimer=None):
    children = [
        html.H2([
            html.Span(number, className="question-number"),
            html.Span(title),
        ], className="question-heading"),
        html.P(id=answer_id, className="section-answer"),
        html.Div(cards, className="section-cards"),
    ]
    if disclaimer:
        children.append(html.P(disclaimer, className="section-disclaimer"))
    return html.Section(children, className=f"question-section {section_class}")


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
    ], className="dashboard-header"),
    html.Main([
        html.Section([
            html.H2("💡 ข้อมูลสำคัญจากตัวกรองปัจจุบัน", className="insight-heading"),
            html.Div(id="key-insights", className="key-insights"),
        ], className="key-insights-wrap"),
        dbc.Alert([
            html.Strong("⚠️ ข้อจำกัดในการตีความ: "),
            html.Span(CAUSAL_DISCLAIMER),
        ], className="viya-disclaimer"),
        dbc.Alert(id="integrity-warning", color="danger", is_open=False, className="integrity-warning"),
        html.Section([
            html.Div([
                html.Label("ช่วงปี ค.ศ.", className="filter-label"),
                html.Div([
                    dcc.RangeSlider(
                        id="filter-year",
                        min=year_ce_min,
                        max=year_ce_max,
                        step=1,
                        value=[year_ce_min, year_ce_max],
                        marks={year: str(year) for year in range(year_ce_min, year_ce_max + 1)},
                    ),
                    html.Div([
                        dcc.Input(
                            id="filter-year-start",
                            type="number",
                            min=year_ce_min,
                            max=year_ce_max,
                            step=1,
                            value=year_ce_min,
                            debounce=True,
                            className="year-input",
                        ),
                        html.Span("–", className="year-separator"),
                        dcc.Input(
                            id="filter-year-end",
                            type="number",
                            min=year_ce_min,
                            max=year_ce_max,
                            step=1,
                            value=year_ce_max,
                            debounce=True,
                            className="year-input",
                        ),
                    ], className="year-inputs"),
                ], className="filter-years"),
            ], className="filter-field filter-year-field"),
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
                html.Div([
                    html.Span("ตัวกรองที่ใช้:"),
                    html.Span(id="filter-pills-container", className="filter-pills"),
                ], className="filter-actions-status"),
                dbc.Button("ล้างตัวกรอง", id="btn-reset", color="danger", outline=True, size="sm"),
            ], className="filter-actions"),
        ], className="filter-bar"),
        html.Div([
            question_section("1", "จุดความร้อนเกิดขึ้นเมื่อไร?", "answer-when", [
                chart_card("ช่วงเวลาที่พบจุดความร้อนมาก", html.Div(id="top-hours-list")),
                chart_card(
                    "รูปแบบจุดความร้อนรายเดือน (คลิกแท่งเพื่อกรอง)",
                    dcc.Graph(id="chart-activity", style={"height": "290px"}),
                    wide=True,
                ),
                chart_card(
                    "สัดส่วนตามฤดูกาล (คลิกแท่งเพื่อกรอง)",
                    dcc.Graph(id="chart-seasonality", style={"height": "225px"}),
                    wide=True,
                ),
            ], "section-when"),
            question_section("2", "จุดความร้อนอยู่ที่ไหน?", "answer-where", [
                chart_card(
                    "แผนที่จุดความร้อน (คลิกจุดเพื่อเลือกตำบล)",
                    html.Div([
                        html.P(MAP_CRS_NOTE, className="map-crs-note"),
                        dcc.Graph(
                            id="spatial-map",
                            style={"height": "420px"},
                            config={"displayModeBar": True, "scrollZoom": True},
                        ),
                    ]),
                    wide=True,
                    action=dbc.RadioItems(
                        id="map-basemap",
                        options=[
                            {"label": "ดาวเทียม", "value": "satellite"},
                            {"label": "มืด", "value": "carto-darkmatter"},
                            {"label": "ถนน", "value": "open-street-map"},
                        ],
                        value="satellite",
                        inline=True,
                        className="map-basemap-options",
                    ),
                ),
                chart_card(
                    "ระดับความเชื่อมั่น (คลิกวงแหวนเพื่อกรอง)",
                    dcc.Graph(id="chart-conf-donut", style={"height": "240px"}),
                ),
                chart_card(
                    "จุดความร้อนแยกตามประเภทป่า (คลิกแท่งเพื่อกรอง)",
                    dcc.Graph(id="chart-pa-treemap", style={"height": "240px"}),
                ),
            ], "section-where"),
            question_section("3", "ข้อมูลพื้นที่ทุเรียนและจุดความร้อน", "answer-durian", [
                chart_card(
                    "ค่าเฉลี่ยจุดความร้อนตามกลุ่มพื้นที่ทุเรียน",
                    dcc.Graph(id="chart-simple-comparison", style={"height": "250px"}),
                ),
                chart_card("รายละเอียดกลุ่มข้อมูล", html.Div(id="dynamic-context-card")),
                chart_card(
                    "ตารางพื้นที่ทุเรียนรายตำบล (คลิกแถวเพื่อกรอง)",
                    html.Div(id="durian-table-container"),
                    wide=True,
                ),
            ], "section-durian", disclaimer=CAUSAL_DISCLAIMER),
            question_section("4", "แนวโน้มข้อมูลตามช่วงเวลา", "answer-trends", [
                chart_card(
                    "พื้นที่ปลูกทุเรียนรายปี",
                    dcc.Graph(id="chart-durian-trend", style={"height": "300px"}),
                    wide=True,
                ),
            ], "section-trends"),
        ], className="question-grid"),
        html.Footer("หอดูดาวข้อมูลจังหวัดกาญจนบุรี", className="page-footer"),
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


@app.callback(
    Output("filter-year", "value"),
    Output("filter-year-start", "value"),
    Output("filter-year-end", "value"),
    Input("filter-year", "value"),
    Input("filter-year-start", "value"),
    Input("filter-year-end", "value"),
    prevent_initial_call=True,
)
def sync_year_controls(year_range, start_year, end_year):
    if ctx.triggered_id == "filter-year":
        return dash.no_update, int(year_range[0]), int(year_range[1])

    if start_year is None or end_year is None:
        return dash.no_update, dash.no_update, dash.no_update

    start_year = max(year_ce_min, min(year_ce_max, int(start_year)))
    end_year = max(year_ce_min, min(year_ce_max, int(end_year)))
    start_year, end_year = sorted((start_year, end_year))
    if list(year_range) == [start_year, end_year]:
        return dash.no_update, start_year, end_year
    return [start_year, end_year], start_year, end_year


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
            font=dict(color="#E2E8F0", family="Sarabun, Inter", size=12),
            margin=m if m is not None else dict(l=25, r=15, t=25, b=25),
        )
        d.update(kwargs)
        return d

    # ── 3. Scorecard values ───────────────────────────────────
    cur_hotspots = metrics["hotspot_total"]

    integrity_warning = None
    integrity_warning_open = False
    is_unfiltered = (
        not any(state.values())
        and list(year_range) == [year_ce_min, year_ce_max]
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
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
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
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=12)),
            annotations=[dict(text=f"<b>{center_text}</b><br><span style='font-size:12px'>TOTAL</span>",
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
            textfont=dict(color="#FFFFFF", size=12, family="Sarabun", weight="bold")
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
    avg_has = group_has["hotspot_count"].mean() if n_has > 0 else 0.0
    avg_no  = group_no["hotspot_count"].mean() if n_no > 0 else 0.0
    sum_has = group_has["hotspot_count"].sum()
    sum_no  = group_no["hotspot_count"].sum()
    if n_has and n_no:
        answer_durian = (
            f"ค่าเฉลี่ยจุดความร้อนในระเบียนพื้นที่ทุเรียนมากกว่า 0.0 ไร่ "
            f"คือ {avg_has:.1f} จุด (n={n_has:,}); ระเบียน 0.0 ไร่ "
            f"คือ {avg_no:.1f} จุด (n={n_no:,})"
        )
    elif n_has:
        answer_durian = f"ระเบียนพื้นที่ทุเรียนมากกว่า 0.0 ไร่มีค่าเฉลี่ย {avg_has:.1f} จุด (n={n_has:,})"
    elif n_no:
        answer_durian = f"ระเบียนพื้นที่ทุเรียน 0.0 ไร่มีค่าเฉลี่ย {avg_no:.1f} จุด (n={n_no:,})"
    elif n_missing:
        answer_durian = (
            f"พบระเบียนพื้นที่ทุเรียนที่ไม่มีค่า {n_missing:,} ตำบล-ปี "
            "และไม่มีระเบียนพื้นที่ตัวเลขให้เปรียบเทียบ"
        )
    else:
        answer_durian = "ไม่พบระเบียนพื้นที่ทุเรียนในช่วงตัวกรองที่เลือก"

    comp_rows = []
    if n_has:
        comp_rows.append({
            "กลุ่ม": f"ปลูกทุเรียน (>0 ไร่)<br>(n={n_has})",
            "ค่าเฉลี่ย": avg_has,
            "จำนวน": n_has,
        })
    if n_no:
        comp_rows.append({
            "กลุ่ม": f"ไม่ปลูก (0 ไร่)<br>(n={n_no})",
            "ค่าเฉลี่ย": avg_no,
            "จำนวน": n_no,
        })
    if comp_rows:
        comp_df = pd.DataFrame(comp_rows)
        fig_comp = px.bar(
            comp_df, x="กลุ่ม", y="ค่าเฉลี่ย",
            color="กลุ่ม",
            text=comp_df.apply(lambda r: f"{r['ค่าเฉลี่ย']:.1f} จุด (n={r['จำนวน']})", axis=1),
            color_discrete_sequence=["#84CC16", "#64748B"],
        )
        fig_comp.update_traces(textposition="outside", textfont=dict(size=12, color="#F8FAFC"))
        fig_comp.update_layout(
            **get_theme(
                m=dict(l=30, r=10, t=25, b=30),
                showlegend=False,
            )
        )
        fig_comp.update_yaxes(gridcolor="#1E293B")
        fig_comp.update_xaxes(gridcolor="#1E293B")
    else:
        fig_comp = go.Figure()
        fig_comp.add_annotation(
            text="ไม่พบข้อมูลพื้นที่ทุเรียนในช่วงตัวกรองที่เลือก",
            showarrow=False,
            font=dict(size=12, color="#94A3B8"),
        )
        fig_comp.update_layout(**get_theme())

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
                f"ระเบียนพื้นที่ทุเรียนที่บันทึกเป็น 0.0 ไร่: {n_no:,} ตำบล-ปี; "
                f"ระเบียนที่ไม่มีค่า (Missing): {n_missing:,} ตำบล-ปี",
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
                font=dict(size=12, color="#FFFFFF")
            )
        )

    # ── 12. Durian Cultivation Ranking Table ────────────────────
    tbl_group = df_d.groupby(["อำเภอ_norm", "ตำบล_norm"]).agg(
        avg_rai=("durian_area_rai", "mean"),
        latest_rai=("durian_area_rai", lambda x: x.iloc[-1] if len(x)>0 else np.nan),
    ).reset_index()
    table_hotspot_counts = (
        df_h.groupby(["อำเภอ_norm", "ตำบล_norm"])
        .size()
        .rename("total_hotspots")
        .reset_index()
    )
    tbl_group = tbl_group.merge(
        table_hotspot_counts,
        on=["อำเภอ_norm", "ตำบล_norm"],
        how="left",
        validate="one_to_one",
    )
    tbl_group["total_hotspots"] = tbl_group["total_hotspots"].fillna(0).astype(int)

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
            title=dict(text=tr_title, font=dict(size=12, color="#94A3B8"))
        )
    )
    fig_durian_line.update_xaxes(tickmode="linear", tick0=2561, dtick=1, gridcolor="#1E293B")
    fig_durian_line.update_yaxes(gridcolor="#1E293B")

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
