"""Journey 5: Utility Content Gate (Rahul + vid_008)

Utility videos skip the learning loop entirely. No recap, no quiz, no recall.
Demonstrates the content type gate.

All data flows through the FastAPI server over HTTP.
"""

import streamlit as st

from demo import api_client

from demo.components.html_blocks import event_card, learner_visible_card, journey_prestart_card, step_nav, system_code_block, step_columns
from demo.components.user_panel import (
    render_panel_header as render_learner_header,
    render_user_profile,
    render_recommendation,
    render_journey_complete,
)
from demo.components.system_panel import (
    render_panel_header as render_system_header,
    render_classification,
    render_recommendation_breakdown,
    render_reasoning_log,
    render_skipped_steps,
)
from demo.components.state_display import render_knowledge_chart, render_knowledge_json


USER_ID = "rahul"
VIDEO_ID = "vid_008"
PREFIX = "j5"


def _get_step():
    return st.session_state.get(f"{PREFIX}_step", 0)


def _set_step(step):
    st.session_state[f"{PREFIX}_step"] = step


def render():
    step = _get_step()

    if step == 0:
        _render_prestart()
        return

    if step == 1:
        _render_profile()
    elif step == 2:
        _render_video_complete()
    elif step == 3:
        _render_skipped()
    elif step == 4:
        _render_recommendation()


def _render_prestart():
    journey_prestart_card(
        "Journey 5: Utility Content Gate",
        "No Preprocess button — utility videos have no concept taxonomy. "
        "The absence itself demonstrates the content type gate before "
        "the journey even begins.",
        "User: Rahul (IS, New) · Video: vid_008 — How to Get Your PAN Card (Utility)",
    )

    if st.button("Start Journey", key=f"{PREFIX}_start", type="primary"):
        _set_step(1)
        st.rerun()


def _render_profile():
    if f"{PREFIX}_user_data" not in st.session_state:
        try:
            st.session_state[f"{PREFIX}_user_data"] = api_client.get_user(USER_ID)
        except Exception as e:
            st.error(f"Could not reach API server: {e}")
            return

    user_data = st.session_state[f"{PREFIX}_user_data"]

    left, right = step_columns("j5_s1")
    with left:
        render_learner_header()
        render_user_profile(user_data)
        render_knowledge_chart(user_data["knowledge_state"], "Current Knowledge")
    with right:
        render_system_header()
        render_knowledge_json(user_data["knowledge_state"], "Raw Knowledge State")

    step_nav(PREFIX, 1, 4, _set_step)


def _render_video_complete():
    if f"{PREFIX}_loop_data" not in st.session_state:
        try:
            st.session_state[f"{PREFIX}_loop_data"] = api_client.video_complete(USER_ID, VIDEO_ID, 1.0)
        except Exception as e:
            st.error(f"API error during video completion: {e}")
            return

    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = step_columns("j5_s2")
    with left:
        render_learner_header()
        event_card("Video Watched",
                   "How to Get Your PAN Card<br>Sarkari Kaam &middot; Utility content")
    with right:
        render_system_header()
        render_classification(loop_data["classification"])

    step_nav(PREFIX, 2, 4, _set_step)


def _render_skipped():
    left, right = step_columns("j5_s3")
    with left:
        render_learner_header()
        learner_visible_card("Pipeline Complete",
                             "Learning loop skipped — utility content. Recommendations only.")
    with right:
        render_system_header()
        render_skipped_steps([
            ("Preprocessing", "No concept taxonomy for utility content"),
            ("Watch Bump", "No knowledge state to update"),
            ("Recap", "No concept profile exists"),
            ("Quiz", "No questions generated"),
            ("Recall", "No spaced repetition for utility"),
        ])
        system_code_block("Content Type Gate",
                          'content_type = "utility"\n'
                          "→ learning loop = OFF\n"
                          "→ recommendation engine only")

    step_nav(PREFIX, 3, 4, _set_step)


def _render_recommendation():
    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = step_columns("j5_s4")
    with left:
        render_learner_header()
        st.markdown("**Recommendations — next videos:**")
        render_recommendation(loop_data.get("recommendation", {}))
        render_journey_complete("Utility Content Gate — Rahul + vid_008")
    with right:
        render_system_header()
        render_recommendation_breakdown(loop_data.get("recommendation", {}))
        system_code_block("Utility Recommendation Mix",
                          "slot_2_distribution:\n"
                          "  50%  same utility category\n"
                          "  30%  other utility categories\n"
                          "  20%  aspiration (cross-pollination)\n"
                          "\n"
                          "pool: series representatives (one per series)\n"
                          "no gap scoring — bucket sampling only")
        render_reasoning_log(loop_data.get("reasoning", []), "Full Pipeline Log")

    step_nav(PREFIX, 4, 4, _set_step)
