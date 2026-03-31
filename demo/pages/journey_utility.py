"""Journey 5: Utility Content Gate (Rahul + vid_008)

Utility videos skip the learning loop entirely. No recap, no quiz, no recall.
"""

import streamlit as st

from db.base import SessionLocal
from db.operations import get_user
from engine.loop import run_video_complete_loop

from demo.components.user_panel import render_user_profile, render_recommendation
from demo.components.system_panel import (
    render_classification, render_recommendation_breakdown, render_reasoning_log,
)
from demo.components.state_display import render_knowledge_chart
from demo.pages.journey_core import _extract_user_data, _extract_loop_result


USER_ID = "rahul"
VIDEO_ID = "vid_008"
PREFIX = "j5"


def _get_step():
    return st.session_state.get(f"{PREFIX}_step", 0)


def _set_step(step):
    st.session_state[f"{PREFIX}_step"] = step


def render():
    st.title("Journey 5: Utility Content Gate")
    st.caption("Rahul watches vid_008 (How to Get Your PAN Card, Utility)")

    step = _get_step()

    if step == 0:
        _render_prestart()
    elif step == 1:
        _render_profile()
    elif step == 2:
        _render_video_complete()
    elif step == 3:
        _render_skipped()
    elif step == 4:
        _render_recommendation()


def _render_prestart():
    st.markdown(
        "No Preprocess button here. Utility videos have no concept taxonomy or LLM-generated artifacts. "
        "This absence demonstrates the content type gate."
    )

    if st.button("Start Journey", key=f"{PREFIX}_start", type="primary"):
        _set_step(1)
        st.rerun()


def _render_profile():
    st.markdown("### User Profile")

    if f"{PREFIX}_user_data" not in st.session_state:
        db = SessionLocal()
        try:
            user = get_user(db, USER_ID)
            st.session_state[f"{PREFIX}_user_data"] = _extract_user_data(user)
        finally:
            db.close()

    user_data = st.session_state[f"{PREFIX}_user_data"]

    left, right = st.columns(2)
    with left:
        render_user_profile(user_data)
    with right:
        render_knowledge_chart(user_data["knowledge_state"], "Current Knowledge")

    if st.button("Next", key=f"{PREFIX}_to_step2", type="primary"):
        _set_step(2)
        st.rerun()


def _render_video_complete():
    st.markdown("### Video Complete")

    if f"{PREFIX}_loop_data" not in st.session_state:
        db = SessionLocal()
        try:
            result = run_video_complete_loop(db, USER_ID, VIDEO_ID, 1.0)
            st.session_state[f"{PREFIX}_loop_data"] = _extract_loop_result(result)
        finally:
            db.close()

    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = st.columns(2)
    with left:
        st.markdown(f"Rahul watched **How to Get Your PAN Card** (`{VIDEO_ID}`)")
        st.markdown("Content type: **utility**. Learning loop does not fire.")
    with right:
        render_classification(loop_data["classification"])

    if st.button("Next", key=f"{PREFIX}_to_step3", type="primary"):
        _set_step(3)
        st.rerun()


def _render_skipped():
    st.markdown("### Content Type Gate")

    left, right = st.columns(2)
    with left:
        st.info("Here's what to watch next.")
        st.caption("No recap, no quiz, no recall for utility content.")
    with right:
        steps = [
            ("Preprocessing", "No concept taxonomy"),
            ("Watch Bump", "No knowledge state to update"),
            ("Recap", "No concept profile"),
            ("Quiz", "No questions generated"),
            ("Recall", "No spaced repetition"),
        ]
        for step_name, reason in steps:
            with st.container(border=True):
                st.markdown(f"~~{step_name}~~ {reason}")

    if st.button("Next", key=f"{PREFIX}_to_step4", type="primary"):
        _set_step(4)
        st.rerun()


def _render_recommendation():
    st.markdown("### Recommendations (50/30/20)")

    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = st.columns(2)
    with left:
        render_recommendation(loop_data.get("recommendation", {}))
        st.success("Journey 5 Complete")
    with right:
        render_recommendation_breakdown(loop_data.get("recommendation", {}))

        st.markdown("##### Utility Buckets")
        st.markdown("- **50%** same utility category")
        st.markdown("- **30%** other utility categories")
        st.markdown("- **20%** aspiration (cross-pollination)")
        st.caption("No gap scoring. Pool uses series representatives.")

        render_reasoning_log(loop_data.get("reasoning", []), "Full reasoning")
