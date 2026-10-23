# tabs/tab2_durian.py — Tab 2: Durian Cultivation
"""
BRD Tab 2:
- Line chart: แนวโน้มพื้นที่ปลูกทุเรียนรายปี (2561–2568)
- Data Table จัดอันดับ (อำเภอ/ตำบล)
- Rules: แสดงหน่วย "ไร่" ชัดเจน, ไฮไลท์ Zero vs Missing
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLORS
from utils.data_loader import load_joined_table


def layout():
    return dbc.Container([
        # ── Controls ───────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Label("แสดงผลระดับ", className="filter-label"),
                dcc.RadioItems(
                    id="t2-level",
                    options=[
                        {"label": " อำเภอ", "value": "อำเภอ_norm"},
                        {"label": " ตำบล",  "value": "ตำบล_norm"},
                    ],
                    value="อำเภอ_norm",
                    inline=True,
                ),
            ], md=4),
            dbc.Col([
                html.Label("เลือกอำเภอ", className="filter-label"),
                dcc.Dropdown(
                    id="t2-amphoe-dd",
                    multi=True,
                    placeholder="ทั้งหมด",
                    style={"color": "#000"},
                ),
            ], md=8),
        ], className="filter-row mb-3"),

        # ── Line chart ─────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 แนวโน้มพื้นที่ปลูกทุเรียนรายปี (หน่วย: ไร่)"),
                    dbc.CardBody([
                        html.P(
                            "⚠️ หมายเหตุ: เส้นที่ขาดหาย = ไม่มีข้อมูลสำรวจ (Missing ≠ ปลูก 0 ไร่)",
                            className="text-warning small mb-1"
                        ),
                        dcc.Graph(id="t2-line-trend", style={"height": "360px"}),
                    ]),
                ], className="dark-card"),
            ], md=12),
        ], className="mb-3"),

        # ── Ranking Table ──────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🏆 ตารางจัดอันดับพื้นที่ปลูกทุเรียน (เฉลี่ยทุกปี)"),
                    dbc.CardBody([
                        html.P(
                            "🟡 = ปลูก 0 ไร่ (สำรวจแล้วไม่มี) | ⬜ = Missing (ไม่มีข้อมูลสำรวจ)",
                            className="small mb-2",
                            style={"color": COLORS["muted"]},
                        ),
                        html.Div(id="t2-table-container"),
                    ]),
                ], className="dark-card"),
            ], md=12),
        ]),
    ], fluid=True)


def register_callbacks(app):

    @app.callback(
        Output("t2-amphoe-dd", "options"),
        Input("t2-level", "value"),
    )
    def update_amphoe_options(level):
        df = load_joined_table()
        opts = [{"label": a, "value": a}
                for a in sorted(df["อำเภอ_norm"].dropna().unique())]
        return opts

    @app.callback(
        Output("t2-line-trend",     "figure"),
        Output("t2-table-container","children"),
        Input("t2-level",           "value"),
        Input("t2-amphoe-dd",       "value"),
    )
    def update_tab2(level, amphoe_sel):
        df = load_joined_table().copy()

        if amphoe_sel:
            df = df[df["อำเภอ_norm"].isin(amphoe_sel)]

        years = sorted(df["พ.ศ."].unique())

        bg = COLORS["card"]
        txt = COLORS["text"]
        layout_base = dict(
            paper_bgcolor=bg, plot_bgcolor=bg,
            font=dict(color=txt, size=12),
            margin=dict(l=40, r=10, t=30, b=40),
        )

        # ── Line chart: aggregate by level + year ──────────────
        grp = df.groupby([level, "พ.ศ."])["durian_area_rai"].sum(min_count=1).reset_index()

        fig_line = px.line(
            grp, x="พ.ศ.", y="durian_area_rai",
            color=level,
            markers=True,
            labels={"พ.ศ.": "ปี พ.ศ.", "durian_area_rai": "พื้นที่ (ไร่)", level: level},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_line.update_layout(**layout_base)
        fig_line.update_xaxes(tickmode="array", tickvals=years)

        # ── Ranking table ──────────────────────────────────────
        pivot = df.groupby(level)["durian_area_rai"].mean().reset_index()
        pivot.columns = [level, "เฉลี่ย (ไร่)"]
        pivot = pivot.sort_values("เฉลี่ย (ไร่)", ascending=False).reset_index(drop=True)
        pivot.index += 1

        # Flag Zero vs Missing
        def flag_cell(val):
            if pd.isna(val):
                return "⬜ Missing"
            if val == 0:
                return f"🟡 0.0"
            return f"{val:,.1f}"

        pivot["เฉลี่ย (ไร่)"] = pivot["เฉลี่ย (ไร่)"].apply(flag_cell)
        pivot.insert(0, "ลำดับ", pivot.index)

        table = dash_table.DataTable(
            data=pivot.to_dict("records"),
            columns=[{"name": c, "id": c} for c in pivot.columns],
            style_header={
                "backgroundColor": COLORS["card_border"],
                "color": COLORS["text"],
                "fontWeight": "bold",
            },
            style_data={
                "backgroundColor": COLORS["card"],
                "color": COLORS["text"],
            },
            style_data_conditional=[
                {
                    "if": {"filter_query": '{เฉลี่ย (ไร่)} contains "Missing"'},
                    "backgroundColor": "#2a2a3a",
                    "color": COLORS["muted"],
                },
                {
                    "if": {"filter_query": '{เฉลี่ย (ไร่)} contains "🟡"'},
                    "backgroundColor": "#3a3a1a",
                    "color": COLORS["warning"],
                },
            ],
            page_size=15,
            sort_action="native",
            style_table={"overflowX": "auto"},
        )

        return fig_line, table
