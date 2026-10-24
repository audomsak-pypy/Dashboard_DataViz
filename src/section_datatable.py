"""
Section 6: Data Details & Tables, Paginated Table, and Annual Durian Trendline.
Fully connected to Centralized Filtered Data.
Kanchanaburi Wildfire & Durian Spatial Analytics.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from src.config import (
    COLOR_DURIAN,
    COLOR_MUTED_GRAY,
    COLOR_BORDER_DARK,
    LAST_UPDATED_DATE,
    TOTAL_DETECTION_DAYS,
    DUPLICATE_COORDS,
    PLOTLY_CONFIG
)
from src.components import render_disclaimer_banner

__all__ = [
    'render_datatable_and_trend_section',
    'render_footer_metadata_bar'
]


def render_datatable_and_trend_section(

    filtered_durian: pd.DataFrame,
    filtered_events: pd.DataFrame,
    sel_years: list = None,
    sel_amp: str = "ทุกอำเภอ"
):
    """
    Renders Paginated Data Table and Annual Trendline (2561-2568)
    strictly bound to filtered_durian and filtered_events.
    """
    st.markdown("<div style='margin-top: 24px; margin-bottom: 12px;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #F0F6FC; font-size: 1.15rem; font-weight: 700;'>ตารางข้อมูลพื้นที่ทุเรียนและจุดความร้อนรายตำบล (Data Table)</h3>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 1. Prepare Table Data from Filtered Dataframes
    col_avg_name = 'เฉลี่ย (พ.ศ. 2561-2568) [ไร่]'
    avg_durian = filtered_durian.groupby(['อำเภอ_norm', 'ตำบล_norm'])['durian_area_rai'].mean().reset_index().rename(
        columns={'durian_area_rai': col_avg_name}
    )

    if sel_years and len(sel_years) == 1:
        target_yr = sel_years[0]
        col_yr_name = f"พ.ศ. {target_yr} (ไร่)"
        durian_yr = filtered_durian[filtered_durian['พ.ศ.'] == target_yr][['อำเภอ_norm', 'ตำบล_norm', 'durian_area_rai']].rename(
            columns={'durian_area_rai': col_yr_name}
        )
    else:
        col_yr_name = "พ.ศ. 2568 (ไร่)"
        durian_yr = filtered_durian[filtered_durian['พ.ศ.'] == 2568][['อำเภอ_norm', 'ตำบล_norm', 'durian_area_rai']].rename(
            columns={'durian_area_rai': col_yr_name}
        )

    # Hotspot count dynamically grouped from filtered_events
    if len(filtered_events) > 0:
        wf_tot = filtered_events.groupby(['อำเภอ_norm', 'ตำบล_norm']).size().reset_index().rename(
            columns={0: 'จุดความร้อน'}
        )
    else:
        wf_tot = pd.DataFrame(columns=['อำเภอ_norm', 'ตำบล_norm', 'จุดความร้อน'])

    merged_table = pd.merge(avg_durian, durian_yr, on=['อำเภอ_norm', 'ตำบล_norm'], how='outer')
    merged_table = pd.merge(merged_table, wf_tot, on=['อำเภอ_norm', 'ตำบล_norm'], how='outer')
    merged_table['จุดความร้อน'] = merged_table['จุดความร้อน'].fillna(0).astype(int)

    # If Amphoe is filtered, restrict table strictly
    if sel_amp != "ทุกอำเภอ":
        merged_table = merged_table[merged_table['อำเภอ_norm'] == sel_amp]

    # Default sort by Hotspot count descending
    merged_table = merged_table.sort_values(by='จุดความร้อน', ascending=False).reset_index(drop=True)
    merged_table.insert(0, 'อันดับ', range(1, len(merged_table) + 1))
    merged_table = merged_table.rename(columns={
        'อำเภอ_norm': 'อำเภอ',
        'ตำบล_norm': 'ตำบล'
    })

    # Search filter input
    search_col, _ = st.columns([1.5, 2])
    with search_col:
        search_kw = st.text_input("ค้นหาตำบลหรืออำเภอ...", placeholder="พิมพ์ชื่ออำเภอหรือตำบลเพื่อกรอง...", key="table_search_input")

    display_table = merged_table.copy()
    if search_kw:
        mask = (
            display_table['อำเภอ'].str.contains(search_kw, na=False) |
            display_table['ตำบล'].str.contains(search_kw, na=False)
        )
        display_table = display_table[mask].reset_index(drop=True)

    # Pagination controls
    page_size = 10
    total_rows = len(display_table)
    total_pages = max((total_rows + page_size - 1) // page_size, 1)

    if 'data_table_page' not in st.session_state:
        st.session_state.data_table_page = 1
    if st.session_state.data_table_page > total_pages:
        st.session_state.data_table_page = total_pages

    start_idx = (st.session_state.data_table_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    page_df = display_table.iloc[start_idx:end_idx].copy()

    # Format numbers for clean presentation
    formatted_page = page_df.copy()
    formatted_page[col_avg_name] = formatted_page[col_avg_name].apply(lambda x: f"{x:,.1f}" if pd.notnull(x) else "—")
    formatted_page[col_yr_name] = formatted_page[col_yr_name].apply(lambda x: f"{x:,.1f}" if pd.notnull(x) else "—")
    formatted_page['จุดความร้อน'] = formatted_page['จุดความร้อน'].apply(lambda x: f"{x:,}")

    # Render Table
    st.dataframe(
        formatted_page,
        use_container_width=True,
        hide_index=True
    )

    # Pagination buttons row
    btn_prev, btn_info, btn_next = st.columns([1, 2, 1])
    with btn_prev:
        if st.button("« หน้าก่อนหน้า", disabled=(st.session_state.data_table_page <= 1), use_container_width=True, key="btn_tbl_prev"):
            st.session_state.data_table_page -= 1
            st.rerun()
    with btn_info:
        st.markdown(
            f"<div style='text-align: center; color: #8B949E; font-size: 0.85rem; padding-top: 6px;'>"
            f"หน้า <b>{st.session_state.data_table_page}</b> จากทั้งหมด <b>{total_pages}</b> หน้า (แสดง {start_idx + 1} - {end_idx} จาก {total_rows} รายการ)"
            f"</div>",
            unsafe_allow_html=True
        )
    with btn_next:
        if st.button("หน้าถัดไป »", disabled=(st.session_state.data_table_page >= total_pages), use_container_width=True, key="btn_tbl_next"):
            st.session_state.data_table_page += 1
            st.rerun()

    # ==========================================
    # 2. Annual Durian & Wildfire Trend (Dual Axis, 2561 - 2568)
    # ==========================================
    st.markdown("<div style='margin-top: 28px; margin-bottom: 12px;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #F0F6FC; font-size: 1.15rem; font-weight: 700;'>แนวโน้มพื้นที่ปลูกทุเรียนและจุดความร้อนรายปี (Dual Axis Trends)</h3>", unsafe_allow_html=True)

    yearly_durian = filtered_durian.groupby('พ.ศ.', as_index=False)['durian_area_rai'].sum()
    yearly_events = filtered_events.groupby('พ.ศ.', as_index=False).size().rename(columns={'size': 'hotspot_count'})

    all_trend_years = sorted(list(set(yearly_durian['พ.ศ.'].dropna().unique()).union(set(yearly_events['พ.ศ.'].dropna().unique()))))
    trend_df = pd.DataFrame({'พ.ศ.': all_trend_years})
    trend_df = trend_df.merge(yearly_durian, on='พ.ศ.', how='left')
    trend_df = trend_df.merge(yearly_events, on='พ.ศ.', how='left')

    if sel_amp != "ทุกอำเภอ":
        durian_title = f"แนวโน้มพื้นที่ปลูกทุเรียนและจุดความร้อน: อำเภอ{sel_amp}"
        durian_sub = f"พื้นที่ทุเรียนปี 2568 ในอำเภอ{sel_amp}: "
    else:
        durian_title = "แนวโน้มพื้นที่ปลูกทุเรียนและจุดความร้อน: ภาพรวมทั้งจังหวัดกาญจนบุรี"
        durian_sub = "พื้นที่ทุเรียนสำหรับ พ.ศ. 2568: "

    durian_2568_tot = yearly_durian[yearly_durian['พ.ศ.'] == 2568]['durian_area_rai'].sum() if 2568 in yearly_durian['พ.ศ.'].values else 0
    st.markdown(f"<div style='color: #8B949E; font-size: 0.85rem;'>{durian_sub}<b>{durian_2568_tot:,.1f}</b> ไร่</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if len(trend_df) > 0:
        fig_line = go.Figure()

        # Trace 1: Durian Area on Y1 (Left axis, Green #84CC16)
        fig_line.add_trace(go.Bar(
            x=trend_df['พ.ศ.'],
            y=trend_df['durian_area_rai'],
            name='พื้นที่ปลูกทุเรียน (ไร่)',
            marker_color='rgba(132, 204, 22, 0.40)',
            marker_line_color='#84CC16',
            marker_line_width=1.5,
            yaxis='y',
            text=trend_df['durian_area_rai'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) and x > 0 else ""),
            textposition='outside',
            textfont=dict(color='#84CC16', size=11)
        ))

        # Trace 2: Hotspot Count on Y2 (Right axis, Fire Red #E53935)
        wf_valid = trend_df.dropna(subset=['hotspot_count']).copy()
        fig_line.add_trace(go.Scatter(
            x=wf_valid['พ.ศ.'],
            y=wf_valid['hotspot_count'],
            name='จำนวนจุดความร้อน (จุด)',
            mode='lines+markers+text',
            line=dict(color='#E53935', width=3),
            marker=dict(size=9, color='#E53935', line=dict(color='#0E1117', width=2)),
            yaxis='y2',
            text=wf_valid['hotspot_count'].apply(lambda x: f"{x:,.0f} จุด" if pd.notnull(x) else ""),
            textposition='top center',
            textfont=dict(color='#FFA726', size=11)
        ))

        max_dur = trend_df['durian_area_rai'].max() or 10
        max_wf = wf_valid['hotspot_count'].max() if len(wf_valid) > 0 else 10

        fig_line.update_layout(
            title=dict(text=durian_title, x=0.02, y=0.96, xanchor='left', yanchor='top'),
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=75, b=65),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=dict(text="พ.ศ.", font=dict(color="#8B949E")), tickmode='linear', tick0=2561, dtick=1),
            yaxis=dict(
                title=dict(text="พื้นที่ปลูกทุเรียน (ไร่)", font=dict(color="#84CC16")),
                tickfont=dict(color="#84CC16"),
                range=[0, max_dur * 1.22]
            ),
            yaxis2=dict(
                title=dict(text="จำนวนจุดความร้อน (จุด)", font=dict(color="#E53935")),
                tickfont=dict(color="#E53935"),
                overlaying="y",
                side="right",
                range=[0, (max_wf or 10) * 1.25]
            ),
            legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_line, use_container_width=True, config=PLOTLY_CONFIG)

        st.markdown(
            "<div style='color: #8B949E; font-size: 0.78rem; margin-top: -12px; margin-bottom: 24px; text-align: center;'>"
            "หมายเหตุ: กราฟแกนร่วม (Dual Axis) แสดงพื้นที่ทุเรียน (แท่งสีเขียว - แกนซ้าย) ควบคู่กับจำนวนจุดความร้อน (เส้นสีแดง - แกนขวา) "
            "โดยข้อมูลจุดความร้อนเริ่มมีการบันทึกเชิงระบบตั้งแต่ พ.ศ. 2566 เป็นต้นไป"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("ไม่มีข้อมูลการเพาะปลูกทุเรียนในพื้นที่ที่เลือก")



def render_footer_metadata_bar():
    """Renders the executive bottom metadata bar."""
    st.markdown(f"""
    <div style="background-color: #161B22; border-top: 1px solid #30363D; padding: 14px 20px; 
                margin-top: 24px; display: flex; flex-wrap: wrap; justify-content: space-around; 
                align-items: center; font-size: 0.82rem; color: #8B949E; border-radius: 6px;">
        <div>อัปเดตข้อมูลล่าสุด: <b style="color: #F0F6FC;">{LAST_UPDATED_DATE}</b></div>
        <div>จำนวนวันที่มีรายงานการตรวจพบ: <b style="color: #F0F6FC;">{TOTAL_DETECTION_DAYS} วัน</b></div>
        <div>พิกัดซ้ำซ้อน: <b style="color: #F0F6FC;">{DUPLICATE_COORDS} จุด</b></div>
    </div>
    """, unsafe_allow_html=True)
