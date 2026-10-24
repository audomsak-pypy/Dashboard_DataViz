"""
Section 1 & 2: Header, Global Top Filters, Key Metrics & Highlights Strip.
Centralized Filter Engine for Kanchanaburi Wildfire & Durian Spatial Analytics.
"""

import streamlit as st
import pandas as pd
from src.config import (
    APP_TITLE,
    APP_SUBTITLE,
    TOTAL_EXPECTED_HOTSPOTS,
    COLOR_FIRE_PRIMARY,
    COLOR_FIRE_ACCENT,
    COLOR_FIRE_LIGHT,
    COLOR_BORDER_DARK,
    PLOTLY_CONFIG
)
from src.components import (
    render_disclaimer_banner,
    render_kpi_card,
    render_highlights_strip,
    create_gauge_meter
)


def render_header_and_filters(df_events: pd.DataFrame, df_durian: pd.DataFrame):
    """
    Centralized Filter Engine:
    Renders Header, Disclaimer, Global Filters Bar, 4 KPI cards, and Highlights strip.
    Returns:
        filtered_events: Wildfire DataFrame filtered by all active criteria.
        filtered_durian: Durian DataFrame filtered by selected Amphoe.
        filtered_joined: Dynamically generated comparison DataFrame at Tambon-Year level.
        filter_desc: Human readable string of active filters.
        filter_meta: Dict containing exact filter values.
    """
    # 1. Header Section
    col_t1, col_t2 = st.columns([3.5, 1.2])
    with col_t1:
        st.markdown(f"<h2 style='margin-bottom: 2px; color: #F0F6FC; font-weight: 700;'>{APP_TITLE}</h2>", unsafe_allow_html=True)
        st.markdown(f"<div style='color: #8B949E; font-size: 0.90rem; margin-bottom: 12px;'>{APP_SUBTITLE} | กรมอุทยานแห่งชาติฯ ร่วมกับ สำนักงานเกษตรจังหวัดกาญจนบุรี</div>", unsafe_allow_html=True)
    with col_t2:
        st.markdown(f"""
        <div style="background-color: #161B22; border: 1px solid #30363D; border-left: 3px solid #E53935; 
                    padding: 8px 14px; border-radius: 6px; text-align: right; margin-top: 6px;">
            <span style="color: #FF7043; font-weight: 600; font-size: 0.82rem;">Data Integrity Verified</span><br/>
            <span style="color: #F0F6FC; font-size: 0.82rem;">Hotspots: <b>{TOTAL_EXPECTED_HOTSPOTS:,}</b> จุด</span>
        </div>
        """, unsafe_allow_html=True)

    # 2. Disclaimer Warning Banner
    render_disclaimer_banner("causal")

    all_years = sorted(df_events['พ.ศ.'].dropna().unique())
    all_amphoe = sorted(df_events['อำเภอ_norm'].dropna().unique())
    all_forest = sorted(df_events['ประเภทป่าอนุรักษ์'].dropna().unique())
    all_conf = ["ทุกระดับ", "high", "nominal", "low"]

    # Initialize session state keys
    if "filter_years_val" not in st.session_state:
        st.session_state.filter_years_val = all_years
    if "filter_amphoe_val" not in st.session_state:
        st.session_state.filter_amphoe_val = "ทุกอำเภอ"
    if "filter_forest_val" not in st.session_state:
        st.session_state.filter_forest_val = "ทุกประเภท"
    if "filter_conf_val" not in st.session_state:
        st.session_state.filter_conf_val = "ทุกระดับ"

    # 3. Top Global Filter Bar
    filter_box = st.container()
    with filter_box:
        st.markdown("""
        <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 12px 18px 4px 18px; margin-bottom: 12px;">
            <div style="font-size: 0.82rem; font-weight: 600; color: #FF7043; margin-bottom: 6px;">ตัวกรองข้อมูลหลัก (Global Filters)</div>
        </div>
        """, unsafe_allow_html=True)

        col_f1, col_f2, col_f3, col_f4, col_btn = st.columns([1.3, 1.3, 1.4, 1.2, 0.9])

        with col_f1:
            sel_years = st.multiselect(
                "ช่วงปี พ.ศ.",
                options=all_years,
                default=st.session_state.filter_years_val,
                key="widget_years"
            )

        with col_f2:
            amp_opts = ["ทุกอำเภอ"] + all_amphoe
            curr_amp_idx = amp_opts.index(st.session_state.filter_amphoe_val) if st.session_state.filter_amphoe_val in amp_opts else 0
            sel_amp = st.selectbox(
                "อำเภอ",
                options=amp_opts,
                index=curr_amp_idx,
                key="widget_amphoe"
            )

        with col_f3:
            forest_opts = ["ทุกประเภท"] + all_forest
            curr_forest_idx = forest_opts.index(st.session_state.filter_forest_val) if st.session_state.filter_forest_val in forest_opts else 0
            sel_forest = st.selectbox(
                "ประเภทป่าอนุรักษ์",
                options=forest_opts,
                index=curr_forest_idx,
                key="widget_forest"
            )

        with col_f4:
            curr_conf_idx = all_conf.index(st.session_state.filter_conf_val) if st.session_state.filter_conf_val in all_conf else 0
            sel_conf = st.selectbox(
                "ความเชื่อมั่น",
                options=all_conf,
                index=curr_conf_idx,
                key="widget_conf"
            )

        with col_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("ล้างตัวกรอง", use_container_width=True, type="secondary"):
                st.session_state.filter_years_val = all_years
                st.session_state.filter_amphoe_val = "ทุกอำเภอ"
                st.session_state.filter_forest_val = "ทุกประเภท"
                st.session_state.filter_conf_val = "ทุกระดับ"
                if "widget_years" in st.session_state:
                    st.session_state.widget_years = all_years
                if "widget_amphoe" in st.session_state:
                    st.session_state.widget_amphoe = "ทุกอำเภอ"
                if "widget_forest" in st.session_state:
                    st.session_state.widget_forest = "ทุกประเภท"
                if "widget_conf" in st.session_state:
                    st.session_state.widget_conf = "ทุกระดับ"
                st.rerun()

    # Update session state with active choices
    st.session_state.filter_years_val = sel_years
    st.session_state.filter_amphoe_val = sel_amp
    st.session_state.filter_forest_val = sel_forest
    st.session_state.filter_conf_val = sel_conf

    # 4. Centralized Data Filtering Engine
    # 4.1 Filter Wildfire Events
    filtered_events = df_events.copy()
    if sel_years:
        filtered_events = filtered_events[filtered_events['พ.ศ.'].isin(sel_years)]
    if sel_amp != "ทุกอำเภอ":
        filtered_events = filtered_events[filtered_events['อำเภอ_norm'] == sel_amp]
    if sel_forest != "ทุกประเภท":
        filtered_events = filtered_events[filtered_events['ประเภทป่าอนุรักษ์'] == sel_forest]
    if sel_conf != "ทุกระดับ":
        filtered_events = filtered_events[filtered_events['CONFEDENCE'] == sel_conf]

    # 4.2 Filter Durian Records (Filtered by Amphoe)
    filtered_durian = df_durian.copy()
    if sel_amp != "ทุกอำเภอ":
        filtered_durian = filtered_durian[filtered_durian['อำเภอ_norm'] == sel_amp]

    # 4.3 Dynamically Build Joined DataFrame from filtered data
    wf_agg_filtered = filtered_events.groupby(
        ['อำเภอ_norm', 'ตำบล_norm', 'พ.ศ.'], as_index=False
    ).agg(hotspot_count=('LAT', 'count'))

    durian_comp = filtered_durian.copy()
    if sel_years:
        durian_comp = durian_comp[durian_comp['พ.ศ.'].isin(sel_years)]
    else:
        durian_comp = durian_comp[durian_comp['พ.ศ.'].isin([2566, 2567, 2568])]

    filtered_joined = pd.merge(
        durian_comp,
        wf_agg_filtered,
        on=['อำเภอ_norm', 'ตำบล_norm', 'พ.ศ.'],
        how='outer'
    )
    filtered_joined['hotspot_count'] = filtered_joined['hotspot_count'].fillna(0).astype(int)
    if sel_amp != "ทุกอำเภอ":
        filtered_joined = filtered_joined[filtered_joined['อำเภอ_norm'] == sel_amp]

    # Active filter status description
    active_filters = []
    if sel_years and set(sel_years) != set(all_years):
        active_filters.append(f"ปี: {', '.join(map(str, sel_years))}")
    if sel_amp != "ทุกอำเภอ":
        active_filters.append(f"อำเภอ: {sel_amp}")
    if sel_forest != "ทุกประเภท":
        active_filters.append(f"ป่า: {sel_forest}")
    if sel_conf != "ทุกระดับ":
        active_filters.append(f"ความเชื่อมั่น: {sel_conf}")

    filter_desc = "ตัวกรองที่ใช้: " + (", ".join(active_filters) if active_filters else "แสดงผลภาพรวมทั้งจังหวัด (ไม่มีตัวกรองเฉพาะ)")
    st.markdown(f"<div style='color: #8B949E; font-size: 0.80rem; margin-top: -6px; margin-bottom: 16px;'>{filter_desc}</div>", unsafe_allow_html=True)

    # 5. Key Metrics & KPIs (Purely based on filtered data)
    count_filtered = len(filtered_events)

    # YTD Delta Calculation (Jan - Aug, month <= 8)
    # Apply active spatial, forest, and confidence filters to baseline
    baseline_events = df_events.copy()
    if sel_amp != "ทุกอำเภอ":
        baseline_events = baseline_events[baseline_events['อำเภอ_norm'] == sel_amp]
    if sel_forest != "ทุกประเภท":
        baseline_events = baseline_events[baseline_events['ประเภทป่าอนุรักษ์'] == sel_forest]
    if sel_conf != "ทุกระดับ":
        baseline_events = baseline_events[baseline_events['CONFEDENCE'] == sel_conf]

    y2568_ytd = len(baseline_events[(baseline_events['พ.ศ.'] == 2568) & (baseline_events['month'] <= 8)])
    y2567_ytd = len(baseline_events[(baseline_events['พ.ศ.'] == 2567) & (baseline_events['month'] <= 8)])

    delta_val = None
    if 2568 in sel_years and y2567_ytd > 0:
        diff_pct = ((y2568_ytd - y2567_ytd) / y2567_ytd) * 100
        delta_val = diff_pct
        delta_str = f"เทียบ YTD (ม.ค.-ส.ค. 2567): {diff_pct:+.1f}%"
    elif len(sel_years) == 1 and sel_years[0] == 2567:
        y2566_cnt = len(baseline_events[baseline_events['พ.ศ.'] == 2566])
        y2567_cnt = len(baseline_events[baseline_events['พ.ศ.'] == 2567])
        if y2566_cnt > 0:
            diff_pct = ((y2567_cnt - y2566_cnt) / y2566_cnt) * 100
            delta_val = diff_pct
            delta_str = f"เทียบ พ.ศ. 2566: {diff_pct:+.1f}%"
        else:
            delta_val = None
            delta_str = f"คิดเป็น {count_filtered / TOTAL_EXPECTED_HOTSPOTS * 100:.1f}% ของทั้งจังหวัด"
    else:
        delta_val = None
        delta_str = f"คิดเป็น {count_filtered / TOTAL_EXPECTED_HOTSPOTS * 100:.1f}% ของทั้งจังหวัด"

    # Durian Area: dynamic based on selected years
    if sel_years and len(sel_years) == 1:
        target_year = sel_years[0]
        durian_latest_rai = filtered_durian[filtered_durian['พ.ศ.'] == target_year]['durian_area_rai'].dropna().sum()
        durian_subtext = f"พ.ศ. {target_year} (ตามปีที่เลือก)"
    else:
        durian_latest_rai = filtered_durian[filtered_durian['พ.ศ.'] == 2568]['durian_area_rai'].dropna().sum()
        durian_subtext = "พ.ศ. 2568 (พื้นที่สำรวจล่าสุด)"

    selected_area_text = sel_amp if sel_amp != "ทุกอำเภอ" else "จังหวัดกาญจนบุรี"

    high_nom_count = len(filtered_events[filtered_events['CONFEDENCE'].isin(['high', 'nominal'])])
    quality_pct = (high_nom_count / count_filtered * 100) if count_filtered > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            title="จุดความร้อนในช่วงที่เลือก",
            value=f"{count_filtered:,} จุด",
            delta=delta_str,
            delta_val=delta_val
        )
    with k2:
        render_kpi_card(
            title="พื้นที่ทุเรียนปีล่าสุดที่เลือก",
            value=f"{durian_latest_rai:,.1f} ไร่",
            delta=durian_subtext
        )
    with k3:
        render_kpi_card(
            title="พื้นที่ที่เลือก",
            value=selected_area_text,
            delta="ขอบเขตการปกครอง"
        )
    with k4:
        render_kpi_card(
            title="คุณภาพข้อมูลจุดความร้อน",
            value=f"{quality_pct:.1f}%",
            delta=f"High/Nominal {high_nom_count:,} จาก {count_filtered:,} จุด"
        )

    # 6. Highlights Strip (01, 02, 03)
    if count_filtered > 0:
        top_month = filtered_events['month_short'].value_counts().index[0]
        top_month_cnt = filtered_events['month_short'].value_counts().iloc[0]
        top_month_pct = (top_month_cnt / count_filtered) * 100
        item1 = f"เดือนสูงสุด: {top_month} ({top_month_pct:.1f}%)"

        top_tambon = filtered_events['ตำบล_norm'].value_counts().index[0]
        top_tambon_cnt = filtered_events['ตำบล_norm'].value_counts().iloc[0]
        item2 = f"ตำบลที่มีจำนวนสูงสุด: {top_tambon} ({top_tambon_cnt:,} จุด)"

        top_hour_win = filtered_events['time_window'].value_counts().index[0].replace(' น.', '')
        top_hour_cnt = filtered_events['time_window'].value_counts().iloc[0]
        top_hour_pct = (top_hour_cnt / count_filtered) * 100
        item3 = f"ชั่วโมงสูงสุด: {top_hour_win} ({top_hour_pct:.1f}%)"
    else:
        item1 = "เดือนสูงสุด: ไม่มีข้อมูลตามตัวกรอง"
        item2 = "ตำบลที่มีจำนวนสูงสุด: ไม่มีข้อมูลตามตัวกรอง"
        item3 = "ชั่วโมงสูงสุด: ไม่มีข้อมูลตามตัวกรอง"

    render_highlights_strip(item1, item2, item3)

    filter_meta = {
        'years': sel_years,
        'amphoe': sel_amp,
        'forest': sel_forest,
        'conf': sel_conf
    }

    return filtered_events, filtered_durian, filtered_joined, filter_desc, filter_meta
