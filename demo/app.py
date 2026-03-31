"""Saathi Demo: Streamlit entry point.

Run from project root:
    streamlit run demo/app.py
"""

import sys
import os

# Ensure project root is on the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Saathi Demo",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Theme selector (since Streamlit chrome is hidden) ---
with st.sidebar:
    theme_choice = st.selectbox(
        "Theme",
        options=["System", "Light", "Dark"],
        index=0,
        key="saathi_theme_choice",
        help="Controls the demo UI theme. System follows your OS setting.",
    )

theme_value = {"System": "system", "Light": "light", "Dark": "dark"}[theme_choice]
components.html(
    f"""
    <script>
      (function() {{
        const theme = {theme_value!r};
        const root = window.parent.document.documentElement;
        if (theme === "system") {{
          root.removeAttribute("data-saathi-theme");
          try {{ window.parent.localStorage.removeItem("saathiTheme"); }} catch (e) {{}}
        }} else {{
          root.setAttribute("data-saathi-theme", theme);
          try {{ window.parent.localStorage.setItem("saathiTheme", theme); }} catch (e) {{}}
        }}
      }})();
    </script>
    """,
    height=0,
)

# --- Hide Streamlit chrome ---
st.markdown("""
<style>
    :root {
        --saathi-border: rgba(0, 0, 0, 0.12);
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --saathi-border: rgba(255, 255, 255, 0.14);
        }
    }
    html[data-theme="dark"], body[data-theme="dark"] {
        --saathi-border: rgba(255, 255, 255, 0.14);
    }

    /* Force theme via in-app selector (set by injected script) */
    html[data-saathi-theme="dark"] {
        color-scheme: dark;
    }
    html[data-saathi-theme="light"] {
        color-scheme: light;
    }
    html[data-saathi-theme="dark"] body {
        background-color: #0e1117;
        color: rgba(250, 250, 250, 0.92);
    }
    html[data-saathi-theme="light"] body {
        background-color: #ffffff;
        color: rgba(0, 0, 0, 0.88);
    }

    /* Hide hamburger menu, footer, header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tighter top padding */
    .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}

    /* Sidebar styling */
    [data-testid="stSidebar"] {background-color: var(--secondary-background-color);}
    [data-testid="stSidebar"] .block-container {padding-top: 1.5rem;}

    /* Cleaner metrics */
    [data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid var(--saathi-border);
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {font-size: 0.8rem; color: var(--text-color); opacity: 0.7;}
    [data-testid="stMetricValue"] {font-size: 1.1rem; font-weight: 600;}

    /* Bordered containers */
    [data-testid="stExpander"] {
        border: 1px solid var(--saathi-border);
        border-radius: 8px;
    }

    /* Step headers */
    h3 {
        border-bottom: 2px solid #4A90D9;
        padding-bottom: 0.4rem;
        margin-bottom: 1rem;
    }

    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background-color: #4A90D9;
        border: none;
        border-radius: 6px;
    }

    /* Dataframe styling */
    .stDataFrame {border-radius: 8px; overflow: hidden;}

    /* Radio buttons - tighter spacing */
    .stRadio > div {gap: 0.3rem;}

    /* Dividers */
    hr {border-color: var(--saathi-border); margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.markdown("## Saathi")
st.sidebar.caption("Personalized learning loop prototype")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select Journey",
    options=[
        "Journey 1: Core Loop",
        "Journey 2: Compare Users",
        "Journey 3: Loop Compounds",
        "Journey 4: Recall",
        "Journey 5: Utility Gate",
        "Sandbox",
    ],
    key="page_selector",
)

st.sidebar.markdown("---")

# Reset button
if st.sidebar.button("Reset Demo", type="secondary"):
    with st.sidebar:
        with st.spinner("Resetting to seed state..."):
            import shutil
            from config.settings import settings
            seed_path = settings.SEED_DB_PATH.replace("sqlite:///", "")
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            shutil.copy2(seed_path, db_path)

    # Clear all session state
    for key in list(st.session_state.keys()):
        if key != "page_selector":
            del st.session_state[key]

    st.sidebar.success("Demo reset to seed state.")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Run order: Journey 1 -> 2 -> 3 -> 4 -> 5")
st.sidebar.caption("Reset restores seed state between runs.")


# --- Page dispatch ---
if page == "Journey 1: Core Loop":
    from demo.pages.journey_core import render
    render()
elif page == "Journey 2: Compare Users":
    from demo.pages.journey_compare import render
    render()
elif page == "Journey 3: Loop Compounds":
    from demo.pages.journey_compound import render
    render()
elif page == "Journey 4: Recall":
    from demo.pages.journey_recall import render
    render()
elif page == "Journey 5: Utility Gate":
    from demo.pages.journey_utility import render
    render()
elif page == "Sandbox":
    from demo.pages.sandbox import render
    render()
