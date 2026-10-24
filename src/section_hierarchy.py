"""
Section 4: Hierarchy & Categorization (Treemap Hierarchy, Top 10 Tambons, Detection Days, and Amphoe Stacked Bar).
Kanchanaburi Wildfire & Durian Spatial Analytics (Ultimate Version).
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from src.config import (
    COLOR_FIRE_PRIMARY,
    COLOR_FIRE_ACCENT,
    COLOR_FIRE_LIGHT,
    PLOTLY_FIRE_SEQUENCE,
    PLOTLY_CONFIG
)


def render_hierarchy_section(filtered_events: pd.DataFrame):
    """
    Renders Treemap Hierarchy, Top 10 Tambons Horizontal Bar,
    Detection Days per Tambon, and Stacked Bar by Amphoe.
    """
    count_filtered = len(filtered_events)
    if count_filtered == 0:
        return

    st.markdown("<div style='margin-top: 28px; margin-bottom: 14px;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #F0F6FC; font-size: 1.15rem; font-weight: 700;'>โครงสร้างประเภทพื้นที่และการกระจายตัวระดับตำบล (Hierarchy & Spatial Ranking)</h3>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Row 1: Treemap Hierarchy & Top 10 Tambons
    col_tree, col_top10 = st.columns([1.15, 1])

    with col_tree:
        area_sizes = filtered_events.groupby(['ประเภทป่าอนุรักษ์', 'ชื่อพื้นที่'], as_index=False).size()
        top_areas = area_sizes.groupby('ชื่อพื้นที่')['size'].sum().nlargest(7).index.tolist()
        tree_data = area_sizes.copy()
        tree_data['ชื่อพื้นที่_grouped'] = tree_data['ชื่อพื้นที่'].apply(lambda x: x if x in top_areas else 'อื่นๆ (Others)')
        tree_df = tree_data.groupby(['ประเภทป่าอนุรักษ์', 'ชื่อพื้นที่_grouped'], as_index=False)['size'].sum().rename(
            columns={'ชื่อพื้นที่_grouped': 'ชื่อพื้นที่'}
        )

        fig_tree = px.treemap(
            tree_df,
            path=['ประเภทป่าอนุรักษ์', 'ชื่อพื้นที่'],
            values='size',
            color='size',
            color_continuous_scale='YlOrRd',
            title="โครงสร้างพื้นที่ป่าอนุรักษ์ (Treemap - Top 7 & อื่นๆ)",
            template="plotly_dark"
        )
        fig_tree.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=75, b=15),
            paper_bgcolor="rgba(0,0,0,0)",
            title=dict(x=0.02, y=0.96, xanchor='left', yanchor='top'),
            coloraxis_colorbar=dict(thickness=12, len=0.8, title="จุด")
        )
        st.plotly_chart(fig_tree, use_container_width=True, config=PLOTLY_CONFIG)

    with col_top10:
        top10_df = filtered_events.groupby(['อำเภอ_norm', 'ตำบล_norm'], as_index=False).size()
        top10_df['label'] = top10_df['ตำบล_norm'] + " - " + top10_df['อำเภอ_norm']
        top10_df = top10_df.sort_values('size', ascending=False).head(10).sort_values('size', ascending=True)

        fig_top10 = px.bar(
            top10_df,
            x='size',
            y='label',
            orientation='h',
            text='size',
            title="10 อันดับตำบลที่มีจุดความร้อนสูงสุด",
            labels={'size': 'จำนวนจุดความร้อน (จุด)', 'label': 'ตำบล - อำเภอ'},
            color='size',
            color_continuous_scale='YlOrRd',
            template="plotly_dark"
        )
        fig_top10.update_layout(
            height=420,
            margin=dict(l=15, r=15, t=75, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=dict(x=0.02, y=0.96, xanchor='left', yanchor='top'),
            coloraxis_showscale=False
        )
        fig_top10.update_traces(texttemplate='%{text:,} จุด', textposition='inside')
        st.plotly_chart(fig_top10, use_container_width=True, config=PLOTLY_CONFIG)

    # Row 2: Detection Days & Stacked Bar by Amphoe
    col_days, col_amp_stack = st.columns([1, 1.15])

    with col_days:
        # Detection days per tambon
        days_df = filtered_events.groupby(['อำเภอ_norm', 'ตำบล_norm'])['date_parsed'].nunique().reset_index()
        days_df.columns = ['อำเภอ_norm', 'ตำบล_norm', 'days_count']
        days_df['label'] = days_df['ตำบล_norm'] + " - " + days_df['อำเภอ_norm']
        days_df = days_df.sort_values('days_count', ascending=False).head(10).sort_values('days_count', ascending=True)

        fig_days = px.bar(
            days_df,
            x='days_count',
            y='label',
            orientation='h',
            text='days_count',
            title="จำนวนวันที่ตรวจพบจุดความร้อนแยกตามตำบล (Top 10)",
            labels={'days_count': 'จำนวนวันตรวจพบ', 'label': 'ตำบล - อำเภอ'},
            color='days_count',
            color_continuous_scale='Blues',
            template="plotly_dark"
        )
        fig_days.update_layout(
            height=380,
            margin=dict(l=15, r=15, t=75, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=dict(x=0.02, y=0.96, xanchor='left', yanchor='top'),
            coloraxis_showscale=False
        )
        fig_days.update_traces(texttemplate='%{text} วัน', textposition='inside')
        st.plotly_chart(fig_days, use_container_width=True, config=PLOTLY_CONFIG)

    with col_amp_stack:
        amp_stack = filtered_events.groupby(['อำเภอ_norm', 'ประเภทป่าอนุรักษ์'], as_index=False).size()
        amp_order = filtered_events['อำเภอ_norm'].value_counts().index.tolist()

        fig_stack = px.bar(
            amp_stack,
            x='อำเภอ_norm',
            y='size',
            color='ประเภทป่าอนุรักษ์',
            category_orders={'อำเภอ_norm': amp_order},
            title="จุดความร้อนแยกตามอำเภอและประเภทป่าอนุรักษ์",
            labels={'size': 'จำนวนจุด (จุด)', 'อำเภอ_norm': 'อำเภอ', 'ประเภทป่าอนุรักษ์': 'ประเภทป่า'},
            color_discrete_sequence=PLOTLY_FIRE_SEQUENCE,
            template="plotly_dark"
        )
        fig_stack.update_layout(
            height=380,
            margin=dict(l=15, r=15, t=75, b=65),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=dict(x=0.02, y=0.96, xanchor='left', yanchor='top'),
            legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5, title_text="")
        )
        st.plotly_chart(fig_stack, use_container_width=True, config=PLOTLY_CONFIG)
