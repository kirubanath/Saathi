"""Journey 1: Core Loop (Priya + vid_001)

Full AS path: video complete -> classification -> recap -> quiz -> evaluation ->
knowledge update -> progress message -> recall scheduling -> recommendation.

All data flows through the FastAPI server over HTTP.
"""

import copy
from datetime import datetime, timezone

import streamlit as st

from demo import api_client
from storage.base import get_storage_client

from demo.components.html_blocks import step_indicator, step_nav, event_card, journey_prestart_card, step_columns
from demo.components.preprocessing_panel import render_preprocessing
from demo.components.user_panel import (
    render_panel_header as render_learner_header,
    render_user_profile,
    render_recap,
    render_quiz,
    render_quiz_results,
    render_recommendation,
    render_progress_message,
    render_journey_complete,
)
from demo.components.system_panel import (
    render_panel_header as render_system_header,
    render_classification,
    render_concept_ranking,
    render_knowledge_comparison,
    render_watch_bump,
    render_recommendation_breakdown,
    render_recall_details,
    render_reasoning_log,
    render_quiz_difficulty,
)
from demo.components.state_display import render_knowledge_chart, render_knowledge_json


USER_ID = "priya"
VIDEO_ID = "vid_001"
PREFIX = "j1"

STEP_LABELS = [
    "Profile", "Video Complete", "Recap",
    "Quiz", "Evaluation", "Progress", "Recall", "Recommendations",
]

_INVALIDATE = {
    5: [f"{PREFIX}_quiz_data", f"{PREFIX}_knowledge_after_quiz", f"{PREFIX}_answers"],
    8: [f"{PREFIX}_completion_time"],
}


def _get_step():
    return st.session_state.get(f"{PREFIX}_step", 0)


def _set_step(step):
    st.session_state[f"{PREFIX}_step"] = step


def render():
    step = _get_step()

    if step == 0:
        _render_prestart()
        return

    st.markdown("#### Journey 1: Core Loop")
    st.caption("Priya (Aspiration Seeker, Warming Up) watches Interview Confidence Ep 1")
    step_indicator(STEP_LABELS, step)

    if step == 1:
        _render_profile()
    elif step == 2:
        _render_video_complete()
    elif step == 3:
        _render_recap()
    elif step == 4:
        _render_quiz()
    elif step == 5:
        _render_quiz_submit()
    elif step == 6:
        _render_knowledge_update()
    elif step == 7:
        _render_recall()
    elif step == 8:
        _render_recommendation()


def _render_prestart():
    journey_prestart_card(
        "Journey 1: Core Loop",
        "The full proactive learning loop: classify → recap → quiz → "
        "knowledge update → schedule recall → recommend.",
        "User: Priya (AS, Warming Up) · Video: vid_001 — Interview Confidence Ep 1",
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
            user_data = api_client.get_user(USER_ID)
        except Exception as e:
            st.error(f"Could not reach API server: {e}")
            return
        st.session_state[f"{PREFIX}_user_data"] = user_data
        st.session_state[f"{PREFIX}_knowledge_before"] = copy.deepcopy(user_data["knowledge_state"])

    user_data = st.session_state[f"{PREFIX}_user_data"]

    left, right = step_columns("j1_s1")
    with left:
        render_learner_header()
        render_user_profile(user_data)
        render_knowledge_chart(user_data["knowledge_state"], "Current Knowledge")
    with right:
        render_system_header()
        render_knowledge_json(user_data["knowledge_state"], "Raw Knowledge State")

    step_nav(PREFIX, 1, 8, _set_step)


def _render_video_complete():
    if f"{PREFIX}_loop_data" not in st.session_state:
        try:
            loop_data = api_client.video_complete(USER_ID, VIDEO_ID, 1.0)
        except Exception as e:
            st.error(f"API error during video completion: {e}")
            return
        st.session_state[f"{PREFIX}_loop_data"] = loop_data
        st.session_state[f"{PREFIX}_knowledge_after_watch"] = copy.deepcopy(loop_data.get("knowledge_after_watch", {}))

    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = step_columns("j1_s2")
    with left:
        render_learner_header()
        event_card("Video Watched",
                   "Interview Confidence Ep 1<br>Body Language in Interviews")
        if loop_data.get("watch_update_delta"):
            items = []
            for concept, d in loop_data["watch_update_delta"].items():
                label = concept.replace("_", " ").title()
                delta = d["after"] - d["before"]
                items.append(f"- {label}: +{delta:.2f}")
            st.markdown("**Knowledge updated after watch:**")
            st.markdown("\n".join(items))
    with right:
        render_system_header()
        render_classification(loop_data["classification"])
        if loop_data.get("watch_update_delta"):
            render_watch_bump(loop_data["watch_update_delta"])

    step_nav(PREFIX, 2, 8, _set_step)


def _render_recap():
    loop_data = st.session_state[f"{PREFIX}_loop_data"]
    recap_bullets = loop_data.get("recap")

    concept_profile = None
    try:
        storage = get_storage_client()
        concept_profile = storage.get_json(f"videos/{VIDEO_ID}/concept_profile.json")
    except Exception:
        pass

    left, right = step_columns("j1_s3")
    with left:
        render_learner_header()
        st.markdown("**Recap — key concepts from this video:**")
        render_recap(recap_bullets or [])
    with right:
        render_system_header()
        render_concept_ranking(recap_bullets or [], concept_profile)
        render_reasoning_log(loop_data.get("recap_reasoning", []), "Recap Engine Logic")

    step_nav(PREFIX, 3, 8, _set_step)


def _render_quiz():
    loop_data = st.session_state[f"{PREFIX}_loop_data"]
    questions = loop_data.get("questions", [])
    knowledge_before = st.session_state.get(f"{PREFIX}_knowledge_before", {})

    left, right = step_columns("j1_s4")
    with left:
        render_learner_header()
        st.markdown("**Quiz — adaptive questions based on knowledge gaps:**")
        answers = render_quiz(questions, PREFIX)
        if answers is not None:
            st.session_state[f"{PREFIX}_answers"] = answers
            _set_step(5)
            st.rerun()
    with right:
        render_system_header()
        render_quiz_difficulty(questions, knowledge_before)

    step_nav(PREFIX, 4, 8, _set_step, show_next=False)


def _render_quiz_submit():
    if f"{PREFIX}_quiz_data" not in st.session_state:
        loop_data = st.session_state[f"{PREFIX}_loop_data"]
        questions_data = loop_data["questions"]
        answers_raw = st.session_state[f"{PREFIX}_answers"]

        answer_items = [
            {"concept": q["concept"], "answer_index": a}
            for q, a in zip(questions_data, answers_raw)
        ]

        try:
            quiz_data = api_client.quiz_submit(USER_ID, VIDEO_ID, questions_data, answer_items)
        except Exception as e:
            st.error(f"API error during quiz submission: {e}")
            return
        st.session_state[f"{PREFIX}_quiz_data"] = quiz_data
        st.session_state[f"{PREFIX}_knowledge_after_quiz"] = copy.deepcopy(quiz_data.get("knowledge_after_quiz", {}))

    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]
    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = step_columns("j1_s5")
    with left:
        render_learner_header()
        render_quiz_results(quiz_data["results"], loop_data["questions"])
    with right:
        render_system_header()
        correct_count = sum(1 for r in quiz_data["results"] if r["correct"])
        total = len(quiz_data["results"])
        st.metric("Score", f"{correct_count}/{total}")
        render_reasoning_log(quiz_data["reasoning"], "Evaluation Logic")

    step_nav(PREFIX, 5, 8, _set_step, invalidate_from=_INVALIDATE)


def _render_knowledge_update():
    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]

    left, right = step_columns("j1_s6")
    with left:
        render_learner_header()
        render_progress_message(quiz_data.get("progress_message"))
        knowledge_after = st.session_state.get(f"{PREFIX}_knowledge_after_quiz", {})
        render_knowledge_chart(knowledge_after, "Updated Knowledge")
    with right:
        render_system_header()
        render_knowledge_comparison(quiz_data["progress"])
        st.caption("`EMA: new = old + 0.3 × (score − old)`")

    step_nav(PREFIX, 6, 8, _set_step, invalidate_from=_INVALIDATE)


def _render_recall():
    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]

    if f"{PREFIX}_completion_time" not in st.session_state:
        st.session_state[f"{PREFIX}_completion_time"] = datetime.now(timezone.utc)

    left, right = step_columns("j1_s7")
    with left:
        render_learner_header()
        recall_details = quiz_data.get("recall_details", [])
        if recall_details:
            from demo.components.html_blocks import learner_visible_card
            learner_visible_card(
                "Recalls Scheduled",
                "<br>".join(
                    f"• {r['concept_key'].split('/', 1)[-1].replace('_', ' ').title()} "
                    f"— review in {r['interval_hours']:.0f}h"
                    for r in recall_details
                ),
            )
    with right:
        render_system_header()
        render_recall_details(
            quiz_data["recalls_scheduled"],
            recall_details=quiz_data.get("recall_details"),
        )
        st.caption("Journey 4 simulates 48h later to surface these recalls.")

    step_nav(PREFIX, 7, 8, _set_step, invalidate_from=_INVALIDATE)


def _render_recommendation():
    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]
    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = step_columns("j1_s8")
    with left:
        render_learner_header()
        st.markdown("**Recommendations — next videos:**")
        render_recommendation(quiz_data.get("recommendation", {}))
        render_journey_complete("The Core Loop — Priya + vid_001")
        knowledge_after = st.session_state.get(f"{PREFIX}_knowledge_after_quiz", {})
        render_knowledge_chart(knowledge_after, "Final Knowledge State")
    with right:
        render_system_header()
        render_recommendation_breakdown(quiz_data.get("recommendation", {}))
        render_reasoning_log(loop_data.get("reasoning", []), "Full Pipeline Log")

    step_nav(PREFIX, 8, 8, _set_step, invalidate_from=_INVALIDATE)
