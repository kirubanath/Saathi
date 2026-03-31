"""Journey 2: Same Video, Different User (Rahul + vid_001)

IS path: video complete -> classification -> IS-toned recap -> no quiz/recall.
Counterfactual proof: same input, different state, different output.

All data flows through the FastAPI server over HTTP.
"""

import streamlit as st

from demo import api_client
from storage.base import get_storage_client

from demo.components.html_blocks import event_card, journey_prestart_card, step_nav, step_columns
from demo.components.preprocessing_panel import render_preprocessing
from demo.components.user_panel import (
    render_panel_header as render_learner_header,
    render_user_profile,
    render_recap,
    render_recommendation,
    render_journey_complete,
)
from demo.components.system_panel import (
    render_panel_header as render_system_header,
    render_classification,
    render_concept_ranking,
    render_watch_bump,
    render_recommendation_breakdown,
    render_reasoning_log,
    render_skipped_steps,
    render_comparison_table,
)
from demo.components.state_display import render_knowledge_chart, render_knowledge_json


USER_ID = "rahul"
VIDEO_ID = "vid_001"
PREFIX = "j2"


def _get_step():
    return st.session_state.get(f"{PREFIX}_step", 0)


def _set_step(step):
    st.session_state[f"{PREFIX}_step"] = step


def render():
    step = _get_step()

    if step == 0:
        _render_prestart()
        return

    st.markdown("#### Journey 2: Same Video, Different User")
    st.caption("Rahul (Information Seeker, New) watches the same vid_001")

    if step == 1:
        _render_profile()
    elif step == 2:
        _render_video_complete()
    elif step == 3:
        _render_recap()
    elif step == 4:
        _render_recommendation()


def _render_prestart():
    journey_prestart_card(
        "Journey 2: Same Video, Different User",
        "Same video as Journey 1, different user. Rahul is an Information Seeker — "
        "he gets an IS-toned recap, no quiz, no recall. "
        "<strong>Counterfactual proof:</strong> same input, different state, different output.",
        "User: Rahul (IS, New) · Video: vid_001 — Interview Confidence Ep 1",
    )

    left_btn, _, right_btn = st.columns([1, 4, 1])
    with left_btn:
        if st.button("Start Journey", key=f"{PREFIX}_start", type="primary"):
            _set_step(1)
            st.rerun()
    with right_btn:
        if st.button("Preprocess vid_001", key=f"{PREFIX}_preprocess"):
            st.session_state[f"{PREFIX}_show_preprocess"] = True

    if st.session_state.get(f"{PREFIX}_show_preprocess"):
        st.markdown("---")
        render_preprocessing(VIDEO_ID)


def _render_profile():
    if f"{PREFIX}_user_data" not in st.session_state:
        try:
            st.session_state[f"{PREFIX}_user_data"] = api_client.get_user(USER_ID)
        except Exception as e:
            st.error(f"Could not reach API server: {e}")
            return

    user_data = st.session_state[f"{PREFIX}_user_data"]

    left, right = step_columns("j2_s1")
    with left:
        render_learner_header()
        render_user_profile(user_data)
        render_knowledge_chart(user_data["knowledge_state"], "Current Knowledge")
    with right:
        render_system_header()
        render_knowledge_json(user_data["knowledge_state"], "Raw Knowledge State")
        st.caption("Compare: Priya is AS/Warming Up with existing knowledge. Rahul is IS/New with none.")

    step_nav(PREFIX, 1, 4, _set_step)


def _render_video_complete():
    if f"{PREFIX}_loop_data" not in st.session_state:
        try:
            st.session_state[f"{PREFIX}_loop_data"] = api_client.video_complete(USER_ID, VIDEO_ID, 1.0)
        except Exception as e:
            st.error(f"API error during video completion: {e}")
            return

    loop_data = st.session_state[f"{PREFIX}_loop_data"]
    c = loop_data["classification"]

    left, right = step_columns("j2_s2")
    with left:
        render_learner_header()
        event_card("Video Watched",
                   "Interview Confidence Ep 1<br>Same video as Priya in Journey 1")
    with right:
        render_system_header()
        render_classification(c)
        render_comparison_table(
            {"user_type": "AS", "quiz": True, "recall": True, "max_bullets": 3},
            {"user_type": c["user_type"], "quiz": c["show_quiz"], "recall": c["show_recall"], "max_bullets": c["max_bullets"]},
        )

    step_nav(PREFIX, 2, 4, _set_step)


def _render_recap():
    loop_data = st.session_state[f"{PREFIX}_loop_data"]
    recap_bullets = loop_data.get("recap")

    concept_profile = None
    try:
        storage = get_storage_client()
        concept_profile = storage.get_json(f"videos/{VIDEO_ID}/concept_profile.json")
    except Exception:
        pass

    left, right = step_columns("j2_s3")
    with left:
        render_learner_header()
        st.markdown("**Recap — IS-toned overview (no quiz path):**")
        render_recap(recap_bullets or [])
    with right:
        render_system_header()
        render_concept_ranking(recap_bullets or [], concept_profile)
        render_skipped_steps([
            ("Quiz", "IS users do not get quizzed"),
            ("Knowledge Update", "No quiz score to apply"),
            ("Recall Scheduling", "IS users have no recall queue"),
        ])

    step_nav(PREFIX, 3, 4, _set_step)


def _render_recommendation():
    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = step_columns("j2_s4")
    with left:
        render_learner_header()
        st.markdown("**Recommendations — next videos:**")
        render_recommendation(loop_data.get("recommendation", {}))
        render_journey_complete("Same Video, Different User — Rahul + vid_001")
    with right:
        render_system_header()
        render_recommendation_breakdown(loop_data.get("recommendation", {}))
        render_reasoning_log(loop_data.get("reasoning", []), "Full Pipeline Log")

    step_nav(PREFIX, 4, 4, _set_step)
