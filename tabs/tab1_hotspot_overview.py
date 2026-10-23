# tabs/tab1_hotspot_overview.py — Tab 1: Hotspot Overview
"""
BRD Tab 1:
- KPI Summary cards
- Map Scatter/Heatmap (LAT/LONG)
- Bar chart: เดือน & ชั่วโมง
- Bar chart: สถานีฯ & CONFEDENCE level
- Filters: ช่วงวันที่, อำเภอ, ตำบล, ประเภทป่าอนุรักษ์
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLORS, MAP_CRS_NOTE, MONTH_LABELS
from utils.data_loader import load_hotspot_events, get_filter_options

# ─── Layout ───────────────────────────────────────────────────
def layout():
    df = load_hotspot_events()
    amphoe_list, tambon_list, pa_types, years_be = get_filter_options(df)

    year_ce_min = int(df["date_parsed"].dt.year.min())
    year_ce_max = int(df["date_parsed"].dt.year.max())

    return dbc.Container([
        # ── Filter row ─────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Label("ช่วงปี (CE)", className="filter-label"),
                dcc.RangeSlider(
                    id="t1-year-slider",
                    min=year_ce_min, max=year_ce_max,
                    step=1,
                    value=[year_ce_min, year_ce_max],
                    marks={y: str(y) for y in range(year_ce_min, year_ce_max + 1)},
                    tooltip={"placement": "bottom"},
                ),
            ], md=4),
            dbc.Col([
                html.Label("อำเภอ", className="filter-label"),
                dcc.Dropdown(
                    id="t1-amphoe-dd",
                    options=[{"label": a, "value": a} for a in amphoe_list],
                    multi=True, placeholder="ทั้งหมด",
                    style={"color": "#000"},
                ),
            ], md=3),
            dbc.Col([
                html.Label("ตำบล", className="filter-label"),
                dcc.Dropdown(
                    id="t1-tambon-dd",
                    options=[{"label": t, "value": t} for t in tambon_list],
                    multi=True, placeholder="ทั้งหมด",
                    style={"color": "#000"},
                ),
            ], md=3),
            dbc.Col([
                html.Label("ประเภทป่าอนุรักษ์", className="filter-label"),
                dcc.Dropdown(
                    id="t1-pa-dd",
                    options=[{"label": p, "value": p} for p in pa_types],
                    multi=True, placeholder="ทั้งหมด",
                    style={"color": "#000"},
                ),
            ], md=2),
        ], className="filter-row mb-3"),

        # ── KPI Cards ──────────────────────────────────────────
        dbc.Row(id="t1-kpi-row", className="mb-3"),

        # ── Map ────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🗺️ แผนที่จุดความร้อน (Hotspot Map)"),
                    dbc.CardBody([
                        html.P(MAP_CRS_NOTE,
                               className="text-warning small mb-2"),
                        dcc.RadioItems(
                            id="t1-map-mode",
                            options=[
                                {"label": " Scatter", "value": "scatter"},
                                {"label": " Heatmap", "value": "density"},
                            ],
                            value="scatter",
                            inline=True,
                            className="mb-2",
                        ),
                        dcc.Graph(id="t1-map", style={"height": "480px"}),
                    ]),
                ], className="dark-card"),
            ], md=12),
        ], className="mb-3"),

        # ── Temporal Charts ────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📅 จุดความร้อนรายเดือน"),
                    dbc.CardBody(dcc.Graph(id="t1-bar-month", style={"height": "320px"})),
                ], className="dark-card"),
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🕐 จุดความร้อนรายชั่วโมง (HH:MM)"),
                    dbc.CardBody(dcc.Graph(id="t1-bar-hour", style={"height": "320px"})),
                ], className="dark-card"),
            ], md=6),
        ], className="mb-3"),

        # ── Station & Confidence Charts ────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🏕️ จุดความร้อนแยกตามสถานีควบคุมไฟป่า"),
                    dbc.CardBody(dcc.Graph(id="t1-bar-station", style={"height": "320px"})),
                ], className="dark-card"),
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📡 การกระจายระดับความน่าเชื่อถือ (CONFEDENCE)"),
                    dbc.CardBody(dcc.Graph(id="t1-pie-conf", style={"height": "320px"})),
                ], className="dark-card"),
            ], md=6),
        ], className="mb-3"),

    ], fluid=True)


# ─── Callbacks ────────────────────────────────────────────────
def register_callbacks(app):

    @app.callback(
        Output("t1-kpi-row",    "children"),
        Output("t1-map",        "figure"),
        Output("t1-bar-month",  "figure"),
        Output("t1-bar-hour",   "figure"),
        Output("t1-bar-station","figure"),
        Output("t1-pie-conf",   "figure"),
        Input("t1-year-slider", "value"),
        Input("t1-amphoe-dd",   "value"),
        Input("t1-tambon-dd",   "value"),
        Input("t1-pa-dd",       "value"),
        Input("t1-map-mode",    "value"),
    )
    def update_tab1(year_range, amphoe_sel, tambon_sel, pa_sel, map_mode):
        df = load_hotspot_events().copy()

        # ── Apply filters ──────────────────────────────────────
        df = df[
            (df["date_parsed"].dt.year >= year_range[0]) &
            (df["date_parsed"].dt.year <= year_range[1])
        ]
        if amphoe_sel:
            df = df[df["อำเภอ_norm"].isin(amphoe_sel)]
        if tambon_sel:
            df = df[df["ตำบล_norm"].isin(tambon_sel)]
        if pa_sel:
            df = df[df["ประเภทป่าอนุรักษ์"].isin(pa_sel)]

        n = len(df)
        top_amphoe = df["อำเภอ_norm"].value_counts().idxmax() if n > 0 else "-"
        top_pa     = df["ประเภทป่าอนุรักษ์"].value_counts().idxmax() if n > 0 else "-"
        top_station= df["สถานีฯที่รับผิดชอบ"].value_counts().idxmax() if n > 0 else "-"

        # ── KPI Cards ──────────────────────────────────────────
        def kpi_card(title, value, icon, color):
            return dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.Div(icon, className="kpi-icon"),
                    html.H3(f"{value:,}" if isinstance(value, int) else value,
                            style={"color": color}),
                    html.P(title, className="kpi-label"),
                ])
            ], className="dark-card kpi-card"), md=3)

        kpi_row = [
            kpi_card("จุดความร้อนทั้งหมด",  n,          "🔥", COLORS["primary"]),
            kpi_card("อำเภอสูงสุด",         top_amphoe, "📍", COLORS["secondary"]),
            kpi_card("ประเภทป่าหลัก",        top_pa,     "🌲", COLORS["durian"]),
            kpi_card("สถานีรับผิดชอบสูงสุด", top_station,"🏕️", COLORS["warning"]),
        ]

        bg = COLORS["background"]
        txt = COLORS["text"]
        layout_base = dict(
            paper_bgcolor=COLORS["card"],
            plot_bgcolor=COLORS["card"],
            font=dict(color=txt, size=12),
            margin=dict(l=10, r=10, t=30, b=10),
        )

        # ── Map ────────────────────────────────────────────────
        if n == 0:
            fig_map = go.Figure()
            fig_map.update_layout(**layout_base, title="ไม่มีข้อมูล")
        elif map_mode == "scatter":
            fig_map = px.scatter_map(
                df, lat="LAT", lon="LONG",
                color="ประเภทป่าอนุรักษ์",
                hover_data={"อำเภอ_norm": True, "ตำบล_norm": True,
                            "date_parsed": True, "CONFEDENCE": True,
                            "LAT": False, "LONG": False},
                map_style="open-street-map",
                zoom=8, center={"lat": 14.8, "lon": 98.9},
                opacity=0.7,
                title="จุดความร้อน (Scatter)",
            )
            fig_map.update_layout(paper_bgcolor=COLORS["card"],
                                  font=dict(color=txt),
                                  margin=dict(l=0, r=0, t=30, b=0))
        else:
            fig_map = px.density_map(
                df, lat="LAT", lon="LONG",
                radius=12,
                map_style="open-street-map",
                zoom=8, center={"lat": 14.8, "lon": 98.9},
                color_continuous_scale="YlOrRd",
                title="ความหนาแน่นจุดความร้อน (Heatmap)",
            )
            fig_map.update_layout(paper_bgcolor=COLORS["card"],
                                  font=dict(color=txt),
                                  margin=dict(l=0, r=0, t=30, b=0))

        # ── Monthly bar ────────────────────────────────────────
        month_counts = (
            df.groupby("month").size().reset_index(name="count")
            .sort_values("month")
        )
        month_counts["label"] = month_counts["month"].map(MONTH_LABELS)
        fig_month = px.bar(
            month_counts, x="label", y="count",
            color_discrete_sequence=[COLORS["primary"]],
            labels={"label": "เดือน", "count": "จำนวน Hotspot"},
        )
        fig_month.update_layout(**layout_base)

        # ── Hourly bar ─────────────────────────────────────────
        hour_counts = df.groupby("hour_of_day").size().reset_index(name="count")
        fig_hour = px.bar(
            hour_counts, x="hour_of_day", y="count",
            color_discrete_sequence=[COLORS["secondary"]],
            labels={"hour_of_day": "ชั่วโมง (ท้องถิ่น)", "count": "จำนวน Hotspot"},
        )
        fig_hour.update_layout(**layout_base)

        # ── Station bar ────────────────────────────────────────
        sta_counts = (
            df.groupby("สถานีฯที่รับผิดชอบ").size()
            .reset_index(name="count")
            .sort_values("count", ascending=True)
        )
        fig_station = px.bar(
            sta_counts, x="count", y="สถานีฯที่รับผิดชอบ",
            orientation="h",
            color_discrete_sequence=[COLORS["warning"]],
            labels={"count": "จำนวน Hotspot", "สถานีฯที่รับผิดชอบ": "สถานี"},
        )
        fig_station.update_layout(**layout_base)

        # ── Confidence pie ─────────────────────────────────────
        conf_counts = df["CONFEDENCE"].value_counts().reset_index()
        conf_counts.columns = ["CONFEDENCE", "count"]
        fig_conf = px.pie(
            conf_counts, names="CONFEDENCE", values="count",
            color_discrete_sequence=[COLORS["low"], COLORS["secondary"], COLORS["high"]],
            hole=0.4,
        )
        fig_conf.update_layout(**layout_base)

        return kpi_row, fig_map, fig_month, fig_hour, fig_station, fig_conf
