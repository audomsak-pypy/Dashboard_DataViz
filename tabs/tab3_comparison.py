# tabs/tab3_comparison.py — Tab 3: Spatial & Temporal Comparison
"""
BRD Tab 3:
- Dual-axis line chart (เทียบปีต่อปี 2566–2568)
- Bubble chart: Hotspot Count vs Durian Area (รายตำบล)
- Mann-Whitney U Test: Hotspot Count ระหว่างกลุ่ม (Durian > 0) vs (Durian == 0)
- Causal disclaimer (BRD Section 5)
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from scipy import stats
import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLORS, CAUSAL_DISCLAIMER
from utils.data_loader import load_joined_table


def layout():
    return dbc.Container([
        # ── Disclaimer ─────────────────────────────────────────
        dbc.Alert(
            [html.Strong("⚠️ ข้อควรระวัง: "), CAUSAL_DISCLAIMER],
            color="warning",
            className="mb-3",
        ),

        # ── Year filter for dual-axis ───────────────────────────
        dbc.Row([
            dbc.Col([
                html.Label("เลือกปี พ.ศ. สำหรับเปรียบเทียบ (Dual-Axis)", className="filter-label"),
                dcc.Checklist(
                    id="t3-years",
                    options=[
                        {"label": " 2566", "value": 2566},
                        {"label": " 2567", "value": 2567},
                        {"label": " 2568", "value": 2568},
                    ],
                    value=[2566, 2567, 2568],
                    inline=True,
                ),
            ], md=6),
            dbc.Col([
                html.Label("ระดับการวิเคราะห์ (Bubble Chart)", className="filter-label"),
                dcc.RadioItems(
                    id="t3-bubble-level",
                    options=[
                        {"label": " ตำบล", "value": "ตำบล_norm"},
                        {"label": " อำเภอ", "value": "อำเภอ_norm"},
                    ],
                    value="ตำบล_norm",
                    inline=True,
                ),
            ], md=6),
        ], className="filter-row mb-3"),

        # ── Dual-Axis Line Chart ────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Dual-Axis: Hotspot Count vs พื้นที่ทุเรียน (รายตำบล รายปี)"),
                    dbc.CardBody([
                        html.P(
                            "⚠️ ปี 2566 มีข้อมูล Hotspot เพียงบางเดือน (พ.ย.–ธ.ค.) — ข้อมูลไม่สมบูรณ์",
                            className="text-warning small mb-1"
                        ),
                        dcc.Graph(id="t3-dual-axis", style={"height": "380px"}),
                    ]),
                ], className="dark-card"),
            ], md=12),
        ], className="mb-3"),

        # ── Bubble Chart ───────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🫧 Bubble Chart: Hotspot Count vs พื้นที่ทุเรียน (ไร่)"),
                    dbc.CardBody(dcc.Graph(id="t3-bubble", style={"height": "400px"})),
                ], className="dark-card"),
            ], md=7),

            # ── Mann-Whitney U Test ────────────────────────────
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🔬 Mann-Whitney U Test"),
                    dbc.CardBody([
                        html.P(
                            "เปรียบเทียบ Hotspot Count ระหว่างตำบลที่มีการปลูกทุเรียน (Area > 0) "
                            "และไม่มีการปลูก (Area == 0)",
                            className="small mb-3",
                            style={"color": COLORS["muted"]},
                        ),
                        html.Div(id="t3-stat-result"),
                        html.Hr(style={"borderColor": COLORS["card_border"]}),
                        html.P(
                            "⚠️ " + CAUSAL_DISCLAIMER,
                            className="small",
                            style={"color": COLORS["warning"]},
                        ),
                    ]),
                ], className="dark-card h-100"),
            ], md=5),
        ]),
    ], fluid=True)


def register_callbacks(app):

    @app.callback(
        Output("t3-dual-axis",   "figure"),
        Output("t3-bubble",      "figure"),
        Output("t3-stat-result", "children"),
        Input("t3-years",        "value"),
        Input("t3-bubble-level", "value"),
    )
    def update_tab3(years_sel, bubble_level):
        df = load_joined_table().copy()

        bg  = COLORS["card"]
        txt = COLORS["text"]
        layout_base = dict(
            paper_bgcolor=bg, plot_bgcolor=bg,
            font=dict(color=txt, size=12),
            margin=dict(l=40, r=40, t=40, b=40),
        )

        # ── Dual-Axis: aggregate by ตำบล + พ.ศ. ──────────────
        df_filt = df[df["พ.ศ."].isin(years_sel)] if years_sel else df.iloc[0:0]
        dual = df_filt.groupby("พ.ศ.").agg(
            total_hotspot=("hotspot_count", "sum"),
            total_durian=("durian_area_rai", lambda x: x.sum(min_count=1)),
        ).reset_index()

        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(
            go.Bar(x=dual["พ.ศ."], y=dual["total_hotspot"],
                   name="Hotspot Count",
                   marker_color=COLORS["primary"], opacity=0.85),
            secondary_y=False,
        )
        fig_dual.add_trace(
            go.Scatter(x=dual["พ.ศ."], y=dual["total_durian"],
                       name="พื้นที่ทุเรียน (ไร่)",
                       mode="lines+markers",
                       line=dict(color=COLORS["durian"], width=2.5),
                       marker=dict(size=8)),
            secondary_y=True,
        )
        fig_dual.update_yaxes(title_text="Hotspot Count",      secondary_y=False,
                              gridcolor=COLORS["card_border"])
        fig_dual.update_yaxes(title_text="พื้นที่ทุเรียน (ไร่)", secondary_y=True,
                              gridcolor=COLORS["card_border"])
        fig_dual.update_xaxes(tickmode="array", tickvals=years_sel or [],
                              gridcolor=COLORS["card_border"])
        fig_dual.update_layout(**layout_base,
                               legend=dict(orientation="h", y=1.05))

        # ── Bubble Chart ───────────────────────────────────────
        bubble_df = (
            df.groupby(bubble_level).agg(
                hotspot_count=("hotspot_count", "sum"),
                durian_area_rai=("durian_area_rai", "sum"),
            ).reset_index()
        )
        bubble_df = bubble_df[bubble_df["durian_area_rai"].notna()]

        fig_bubble = px.scatter(
            bubble_df,
            x="durian_area_rai", y="hotspot_count",
            size="hotspot_count",
            color=bubble_level,
            hover_name=bubble_level,
            size_max=60,
            labels={
                "durian_area_rai": "พื้นที่ทุเรียน รวมทุกปี (ไร่)",
                "hotspot_count":   "Hotspot Count รวมทุกปี",
            },
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_bubble.update_layout(**layout_base)

        # ── Mann-Whitney U Test ────────────────────────────────
        # ใช้ระดับ ตำบล-ปี (joined table)
        group_has = df[df["durian_area_rai"] > 0]["hotspot_count"].dropna()
        group_not = df[df["durian_area_rai"] == 0]["hotspot_count"].dropna()

        if len(group_has) >= 2 and len(group_not) >= 2:
            stat, pval = stats.mannwhitneyu(
                group_has, group_not, alternative="two-sided"
            )
            n1, n2 = len(group_has), len(group_not)
            # Effect size: rank-biserial correlation
            r_rb = 1 - (2 * stat) / (n1 * n2)
            effect_label = (
                "เล็กน้อย (small)" if abs(r_rb) < 0.3
                else ("ปานกลาง (medium)" if abs(r_rb) < 0.5
                      else "มาก (large)")
            )
            sig = pval < 0.05

            stat_ui = dbc.Table([
                html.Tbody([
                    html.Tr([html.Th("กลุ่มที่ 1 (Durian > 0)"),
                             html.Td(f"n = {n1} ตำบล-ปี")]),
                    html.Tr([html.Th("กลุ่มที่ 2 (Durian == 0)"),
                             html.Td(f"n = {n2} ตำบล-ปี")]),
                    html.Tr([html.Th("U Statistic"),
                             html.Td(f"{stat:,.2f}")]),
                    html.Tr([html.Th("P-value"),
                             html.Td(
                                 html.Span(
                                     f"{pval:.4f} {'✅ Significant' if sig else '❌ Not significant'} (α=0.05)",
                                     style={"color": COLORS["primary"] if sig else COLORS["muted"]},
                                 )
                             )]),
                    html.Tr([html.Th("Effect size (r)"),
                             html.Td(f"{r_rb:.4f} — {effect_label}")]),
                    html.Tr([html.Th("Median Hotspot (กลุ่ม 1)"),
                             html.Td(f"{group_has.median():.1f}")]),
                    html.Tr([html.Th("Median Hotspot (กลุ่ม 2)"),
                             html.Td(f"{group_not.median():.1f}")]),
                ])
            ], bordered=True, color="dark", hover=True, size="sm")
        else:
            stat_ui = html.P("ข้อมูลไม่เพียงพอสำหรับการทดสอบทางสถิติ",
                             style={"color": COLORS["muted"]})

        return fig_dual, fig_bubble, stat_ui
