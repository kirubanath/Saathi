"""Saathi Demo: Streamlit entry point.

Run from project root:
    streamlit run demo/app.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="Saathi Demo",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important;}
    .block-container {padding-top: 1rem; padding-bottom: 0.5rem; max-width: 1400px;}

    :root {
        --card-learner-bg: rgba(55, 48, 90, 0.25);
        --card-learner-border: rgba(74,144,217,0.30);
        --card-event-bg: rgba(55, 48, 90, 0.18);
        --card-event-border: rgba(128,128,128,0.20);
        --card-system-bg: rgba(55, 48, 90, 0.18);
        --card-system-border: rgba(230,126,34,0.20);
        --card-prestart-bg: rgba(55, 48, 90, 0.18);
        --card-prestart-border: rgba(128,128,128,0.18);
        --card-header-bg: rgba(55, 48, 90, 0.22);
    }

    /* Navigation pills (segmented control) */
    div[data-testid="stSegmentedControl"] {
        border-bottom: 2px solid rgba(128,128,128,0.15);
        padding-bottom: 4px;
    }
    div[data-testid="stSegmentedControl"] button {
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em;
        padding: 8px 18px !important;
        border-radius: 6px 6px 0 0 !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
        font-weight: 700 !important;
    }

    [data-testid="stMetric"] {
        background: transparent;
        border: none;
        padding: 4px 0;
    }
    [data-testid="stMetricLabel"] {font-size: 0.72rem; opacity: 0.6;}
    [data-testid="stMetricValue"] {font-size: 1.1rem; font-weight: 700;}

    .stButton > button {
        border-radius: 8px;
        padding: 8px 32px;
        font-weight: 600;
        font-size: 0.82rem;
        min-height: 42px;
        white-space: nowrap;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100%;
    }
    .stButton > button p,
    .stButton > button div,
    .stButton > button span {
        text-align: center !important;
        width: 100%;
    }
    .stButton > button[kind="primary"] {
        background-color: #4A90D9;
        border: none;
        color: #fff !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #e74c3c !important;
        border: 1px solid #c0392b !important;
        color: #fff !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #c0392b !important;
        border-color: #a93226 !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid rgba(128,128,128,0.12);
        border-radius: 8px;
    }

    .stRadio > div {gap: 0.25rem;}
    hr {border-color: rgba(128,128,128,0.1); margin: 1rem 0;}

</style>
""", unsafe_allow_html=True)

from demo.components.html_blocks import scroll_to_top
scroll_to_top()

# ---------------------------------------------------------------------------
# Title bar with Reset button
# ---------------------------------------------------------------------------
st.markdown(
    '<div style="display:flex;align-items:center;justify-content:space-between;'
    'padding:12px 20px;margin-bottom:8px;'
    'border:1px solid rgba(128,128,128,0.12);border-radius:12px;'
    'background:var(--card-header-bg);">'
    '<div>'
    '<div style="font-size:1.3rem;font-weight:800;letter-spacing:-0.01em;">Saathi Demo</div>'
    '<div style="font-size:0.7rem;opacity:0.5;margin-top:2px;">'
    'Personalized learning loop &nbsp;·&nbsp; Run order: J1 → J2 → J3 → J4 → J5'
    '</div></div>'
    '</div>',
    unsafe_allow_html=True,
)

_, theme_col, reset_col = st.columns([7, 1.5, 1.5])
with theme_col:
    light_mode = st.toggle("☀ Light", value=st.session_state.get("light_mode", False), key="light_mode")
with reset_col:
    if st.button("⟳  Reset Demo", key="reset_demo", type="secondary"):
        with st.spinner("Resetting..."):
            import shutil
            from config.settings import settings
            seed_path = settings.SEED_DB_PATH.replace("sqlite:///", "")
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            shutil.copy2(seed_path, db_path)

        saved_light = st.session_state.get("light_mode", False)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state["light_mode"] = saved_light
        st.rerun()

if light_mode:
    st.markdown("""
<style>
    :root {
        --card-learner-bg: rgba(232, 240, 254, 0.6) !important;
        --card-learner-border: rgba(74,144,217,0.25) !important;
        --card-event-bg: rgba(245, 242, 235, 0.5) !important;
        --card-event-border: rgba(0,0,0,0.10) !important;
        --card-system-bg: rgba(255, 248, 240, 0.5) !important;
        --card-system-border: rgba(230,126,34,0.18) !important;
        --card-prestart-bg: rgba(245, 242, 235, 0.5) !important;
        --card-prestart-border: rgba(0,0,0,0.10) !important;
        --card-header-bg: rgba(232, 240, 254, 0.4) !important;
    }
    :root, [data-testid="stAppViewContainer"], [data-testid="stApp"],
    [data-testid="stHeader"], .main, .block-container,
    [data-testid="stBottomBlockContainer"] {
        background-color: #faf9f7 !important;
        color: #1a1a1a !important;
    }
    [data-testid="stMarkdown"], [data-testid="stText"],
    p, span, div, label, h1, h2, h3, h4, h5, h6, li, td, th, caption {
        color: #1a1a1a !important;
    }
    div[data-testid="stSegmentedControl"] {
        border-bottom-color: rgba(0,0,0,0.1) !important;
    }
    [data-testid="stExpander"] {
        border-color: rgba(0,0,0,0.1) !important;
        background: #f5f2eb !important;
    }
    pre, code { color: #1a1a1a !important; }
    hr { border-color: rgba(0,0,0,0.08) !important; }
    [data-testid="stDataFrame"] { color: #1a1a1a !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navigation (session-state-tracked — survives st.rerun)
# ---------------------------------------------------------------------------
_NAV_OPTIONS = [
    "J1: Core Loop",
    "J2: Compare Users",
    "J3: Compounding",
    "J4: Recall",
    "J5: Utility Gate",
    "Sandbox",
]

active = st.segmented_control(
    "Navigation",
    _NAV_OPTIONS,
    default=_NAV_OPTIONS[0],
    key="active_nav",
    label_visibility="collapsed",
)

if active == "J1: Core Loop":
    from demo.pages.journey_core import render as render_j1
    render_j1()
elif active == "J2: Compare Users":
    from demo.pages.journey_compare import render as render_j2
    render_j2()
elif active == "J3: Compounding":
    from demo.pages.journey_compound import render as render_j3
    render_j3()
elif active == "J4: Recall":
    from demo.pages.journey_recall import render as render_j4
    render_j4()
elif active == "J5: Utility Gate":
    from demo.pages.journey_utility import render as render_j5
    render_j5()
elif active == "Sandbox":
    from demo.pages.sandbox import render as render_sandbox
    render_sandbox()
