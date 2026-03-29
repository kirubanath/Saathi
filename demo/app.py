"""Saathi Demo — two-panel Streamlit app for the proactive learning loop."""

import json
from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"


def main() -> None:
    st.set_page_config(
        page_title="Saathi — AI Learning Companion",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("Saathi — AI Learning Companion")
    st.caption("Prototype demo · Seekho")

    left, right = st.columns([1, 1])

    with left:
        st.subheader("Saathi")
        st.caption("What the learner sees")

    with right:
        st.subheader("System Brain")
        st.caption("What the AI is doing")


if __name__ == "__main__":
    main()
