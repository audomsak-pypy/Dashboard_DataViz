"""
Professional Executive Dashboard: Kanchanaburi Wildfire & Durian Spatial Analytics
Enforces Dark Mode, Custom Fire Palette, Zero Emojis, and Zero Text Truncation.
"""

import streamlit as st
from src.config import (
    APP_TITLE,
    APP_SUBTITLE,
    TOTAL_EXPECTED_HOTSPOTS
)
from src.data_loader import load_and_process_data
from src.tab_hotspots import render_tab_hotspots
from src.tab_durian import render_tab_durian
from src.tab_comparison import render_tab_comparison

# Streamlit Page Setup - Wide Layout
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive CSS: Forced Dark Palette & No Text Truncation
st.markdown("""
<style>
    /* Global Background and Typography */
    .stApp {
        background-color: #0E1117 !important;
        color: #F0F6FC !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* Metric Container Cards */
    [data-testid="stMetric"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        margin-bottom: 8px !important;
    }

    /* Metric Label - Full Wrapping & No Truncation */
    [data-testid="stMetricLabel"] {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        color: #8B949E !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        line-height: 1.3 !important;
    }

    /* Metric Value - Full Visibility, No Ellipsis (...) */
    [data-testid="stMetricValue"] {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        text-overflow: clip !important;
        overflow: visible !important;
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        color: #F0F6FC !important;
        line-height: 1.25 !important;
    }

    /* Metric Delta */
    [data-testid="stMetricDelta"] {
        white-space: normal !important;
        word-break: break-word !important;
        font-size: 0.8rem !important;
    }

    /* Modern Tabs */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #8B949E !important;
        border-bottom: 2px solid transparent !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FF7043 !important;
        border-bottom: 2px solid #E53935 !important;
    }

    /* Expanders & Form Elements */
    [data-testid="stExpander"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        margin-bottom: 16px !important;
    }

    /* Dataframe Header */
    .stDataFrame {
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    /* Spacing */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Executive Header Section (Zero Emojis)
    col_title, col_badge = st.columns([3.2, 0.8])
    with col_title:
        st.title(APP_TITLE)
        st.caption(f"{APP_SUBTITLE} | กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช ร่วมกับ สำนักงานเกษตรจังหวัดกาญจนบุรี")
    with col_badge:
        st.markdown(f"""
        <div style="background-color: #161B22; border: 1px solid #30363D; border-left: 3px solid #E53935; 
                    padding: 8px 12px; border-radius: 6px; text-align: right; margin-top: 10px;">
            <span style="color: #FF7043; font-weight: 600; font-size: 0.82rem;">Data Integrity Verified</span><br/>
            <span style="color: #F0F6FC; font-size: 0.82rem;">Hotspots: <b>{TOTAL_EXPECTED_HOTSPOTS:,}</b> จุด</span>
        </div>
        """, unsafe_allow_html=True)

    # Data Loader
    with st.spinner("กำลังโหลดข้อมูล..."):
        try:
            data = load_and_process_data()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
            st.stop()

    df_events = data['events']
    df_durian = data['durian_raw']
    df_joined = data['joined']
    total_expected = data['total_hotspots']

    # Tab Navigation (Clean Minimalist Labels without Emojis)
    tab1, tab2, tab3 = st.tabs([
        "ภาพรวมจุดความร้อน (Hotspots Overview)",
        "พื้นที่ปลูกทุเรียน (Durian Cultivation)",
        "การเปรียบเทียบเชิงพื้นที่และสถิติ (Spatial & Statistical Comparison)"
    ])

    with tab1:
        render_tab_hotspots(df_events, total_expected)

    with tab2:
        render_tab_durian(df_durian, df_joined)

    with tab3:
        render_tab_comparison(df_joined)

    # Executive Footer
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: #8B949E; font-size: 0.82rem; padding: 16px 0; border-top: 1px solid #30363D;">
        <b>Kanchanaburi Wildfire & Durian Spatial Analytics</b> | พัฒนาด้วย Python, Streamlit และ Plotly<br/>
        ข้อมูลนี้จัดทำเพื่อการวิเคราะห์เชิงวิชาการระดับพื้นที่ปกครอง ปราศจากข้อสรุปเชิงสาเหตุ
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
