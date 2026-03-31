"""Journey 2: Same Video, Different User (Rahul + vid_001)

IS path: video complete -> classification -> IS-toned recap -> no quiz/recall.
"""

import streamlit as st

from db.base import SessionLocal
from db.operations import get_user
from engine.loop import run_video_complete_loop
from storage.base import get_storage_client

from demo.components.preprocessing_panel import render_preprocessing
from demo.components.user_panel import render_user_profile, render_recap, render_recommendation
from demo.components.system_panel import (
    render_classification, render_concept_ranking, render_watch_bump,
    render_recommendation_breakdown, render_reasoning_log,
)
from demo.components.state_display import render_knowledge_chart
from demo.pages.journey_core import _extract_user_data, _extract_loop_result


USER_ID = "rahul"
VIDEO_ID = "vid_001"
PREFIX = "j2"


def _get_step():
    return st.session_state.get(f"{PREFIX}_step", 0)


def _set_step(step):
    st.session_state[f"{PREFIX}_step"] = step


def render():
    st.title("Journey 2: Same Video, Different User")
    st.caption("Rahul (IS, New) watches vid_001 (Interview Confidence Ep 1)")

    step = _get_step()

    if step == 0:
        _render_prestart()
    elif step == 1:
        _render_profile()
    elif step == 2:
        _render_video_complete()
    elif step == 3:
        _render_recap()
    elif step == 4:
        _render_recommendation()


def _render_prestart():
    st.markdown("Same video, different user. Rahul is an Information Seeker: IS-toned recap, no quiz, no recall.")

    col1, col2, _ = st.columns([1, 1, 2])
    with col1:
        if st.button("Preprocess vid_001", key=f"{PREFIX}_preprocess"):
            st.session_state[f"{PREFIX}_show_preprocess"] = True
    with col2:
        if st.button("Start Journey", key=f"{PREFIX}_start", type="primary"):
            _set_step(1)
            st.rerun()

    if st.session_state.get(f"{PREFIX}_show_preprocess"):
        render_preprocessing(VIDEO_ID)


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

    st.caption("Compare: Priya is AS/Warming Up with existing knowledge. Rahul is IS/New with none.")

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
    c = loop_data["classification"]

    left, right = st.columns(2)
    with left:
        st.markdown(f"Rahul watched **Interview Confidence Ep 1** (`{VIDEO_ID}`)")
        if loop_data.get("watch_update_delta"):
            render_watch_bump(loop_data["watch_update_delta"])

        # Compact comparison
        st.markdown("##### Priya vs Rahul")
        st.dataframe({
            "": ["User Type", "Quiz", "Recall", "Max Bullets"],
            "Priya (J1)": ["AS", "Yes", "Yes", "3"],
            "Rahul (J2)": [c["user_type"], "No" if not c["show_quiz"] else "Yes",
                           "No" if not c["show_recall"] else "Yes", str(c["max_bullets"])],
        }, use_container_width=True, hide_index=True)
    with right:
        render_classification(c)

    if st.button("Next", key=f"{PREFIX}_to_step3", type="primary"):
        _set_step(3)
        st.rerun()


def _render_recap():
    st.markdown("### IS-Toned Recap")

    loop_data = st.session_state[f"{PREFIX}_loop_data"]
    recap_bullets = loop_data.get("recap")

    concept_profile = None
    try:
        storage = get_storage_client()
        concept_profile = storage.get_json(f"videos/{VIDEO_ID}/concept_profile.json")
    except Exception:
        pass

    left, right = st.columns(2)
    with left:
        render_recap(recap_bullets or [])
        st.caption("IS tone: informational and neutral, vs Priya's growth-oriented AS tone.")
    with right:
        render_concept_ranking(recap_bullets or [], concept_profile)
        st.caption("IS users: ranked by coverage only (no gap weighting).")

    st.warning("No quiz or recall for IS users. Proceeding to recommendations.")

    if st.button("Next", key=f"{PREFIX}_to_step4", type="primary"):
        _set_step(4)
        st.rerun()


def _render_recommendation():
    st.markdown("### Recommendations")

    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = st.columns(2)
    with left:
        render_recommendation(loop_data.get("recommendation", {}))
        st.success("Journey 2 Complete")
    with right:
        render_recommendation_breakdown(loop_data.get("recommendation", {}))
        render_reasoning_log(loop_data.get("reasoning", []), "Full reasoning")
