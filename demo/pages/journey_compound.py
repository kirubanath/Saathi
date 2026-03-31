"""Journey 3: Loop Compounds (Priya + vid_002)

Same flow as Journey 1 but with vid_002 and post-Journey-1 knowledge state.
Proves the loop adapts based on accumulated state.

All data flows through the FastAPI server over HTTP.
"""

import copy

import streamlit as st

from demo import api_client
from storage.base import get_storage_client

from demo.components.html_blocks import step_indicator, step_nav, event_card, journey_prestart_card, system_json_block, step_columns
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
VIDEO_ID = "vid_002"
PREFIX = "j3"

STEP_LABELS = [
    "Profile", "Video Complete", "Recap",
    "Quiz", "Evaluation", "Progress", "Recall", "Recommendations",
]

_INVALIDATE = {
    5: [f"{PREFIX}_quiz_data", f"{PREFIX}_knowledge_after_quiz", f"{PREFIX}_answers"],
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

    st.markdown("#### Journey 3: Loop Compounds")
    st.caption("Priya watches Interview Confidence Ep 2 with post-Journey-1 knowledge")
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
        "Journey 3: Loop Compounds",
        "Priya follows the Slot 1 pick from Journey 1. Her knowledge shifted, "
        "so concept targeting and quiz difficulty adapt.",
        "User: Priya (AS, Warming Up) · Video: vid_002 — Interview Confidence Ep 2",
    )

    if "j1_step" not in st.session_state or st.session_state.get("j1_step", 0) < 8:
        st.warning("Journey 1 not completed. Run Journey 1 first for the compounding effect.")

    left_btn, _, right_btn = st.columns([1, 4, 1])
    with left_btn:
        if st.button("Start Journey", key=f"{PREFIX}_start", type="primary"):
            _set_step(1)
            st.rerun()
    with right_btn:
        if st.button("Preprocess vid_002", key=f"{PREFIX}_preprocess"):
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

    left, right = step_columns("j3_s1")
    with left:
        render_learner_header()
        render_user_profile(user_data)
        render_knowledge_chart(user_data["knowledge_state"], "Current Knowledge (Post-J1)")
    with right:
        render_system_header()
        render_knowledge_json(user_data["knowledge_state"], "Post-Journey-1 Knowledge")

        j1_before = st.session_state.get("j1_knowledge_before", {})
        if j1_before:
            diffs = {}
            for cat, concepts in user_data["knowledge_state"].items():
                for concept, score in concepts.items():
                    j1_score = j1_before.get(cat, {}).get(concept, 0)
                    if score != j1_score:
                        diffs[concept] = {
                            "j1_start": round(j1_score, 3),
                            "now": round(score, 3),
                            "change": round(score - j1_score, 3),
                        }
            if diffs:
                system_json_block("Changes Since J1 Start", diffs)

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

    left, right = step_columns("j3_s2")
    with left:
        render_learner_header()
        event_card("Video Watched",
                   "Interview Confidence Ep 2<br>Answering Questions with Structure")
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

    left, right = step_columns("j3_s3")
    with left:
        render_learner_header()
        st.markdown("**Recap — key concepts from this video:**")
        render_recap(recap_bullets or [])
    with right:
        render_system_header()
        render_concept_ranking(recap_bullets or [], concept_profile)
        render_reasoning_log(loop_data.get("recap_reasoning", []), "Recap Engine Logic")
        st.caption("Compare ranking with Journey 1 — gaps shifted after J1 quiz.")

    step_nav(PREFIX, 3, 8, _set_step)


def _render_quiz():
    loop_data = st.session_state[f"{PREFIX}_loop_data"]
    questions = loop_data.get("questions", [])
    knowledge_before = st.session_state.get(f"{PREFIX}_knowledge_before", {})

    left, right = step_columns("j3_s4")
    with left:
        render_learner_header()
        st.markdown("**Quiz — difficulty adapts to post-J1 scores:**")
        answers = render_quiz(questions, PREFIX)
        if answers is not None:
            st.session_state[f"{PREFIX}_answers"] = answers
            _set_step(5)
            st.rerun()
    with right:
        render_system_header()
        render_quiz_difficulty(questions, knowledge_before)
        st.caption("Difficulty may shift from J1 — scores changed after J1 quiz.")

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

    left, right = step_columns("j3_s5")
    with left:
        render_learner_header()
        render_quiz_results(quiz_data["results"], loop_data["questions"])
    with right:
        render_system_header()
        correct_count = sum(1 for r in quiz_data["results"] if r["correct"])
        st.metric("Score", f"{correct_count}/{len(quiz_data['results'])}")
        render_reasoning_log(quiz_data["reasoning"], "Evaluation Logic")

    step_nav(PREFIX, 5, 8, _set_step, invalidate_from=_INVALIDATE)


def _render_knowledge_update():
    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]

    left, right = step_columns("j3_s6")
    with left:
        render_learner_header()
        render_progress_message(quiz_data.get("progress_message"))
        knowledge_after = st.session_state.get(f"{PREFIX}_knowledge_after_quiz", {})
        render_knowledge_chart(knowledge_after, "Updated Knowledge")
    with right:
        render_system_header()
        render_knowledge_comparison(quiz_data["progress"])

    step_nav(PREFIX, 6, 8, _set_step, invalidate_from=_INVALIDATE)


def _render_recall():
    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]

    left, right = step_columns("j3_s7")
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

    step_nav(PREFIX, 7, 8, _set_step, invalidate_from=_INVALIDATE)


def _render_recommendation():
    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]
    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = step_columns("j3_s8")
    with left:
        render_learner_header()
        st.markdown("**Recommendations — next videos:**")
        render_recommendation(quiz_data.get("recommendation", {}))
        render_journey_complete("Loop Compounds — Priya + vid_002")
    with right:
        render_system_header()
        render_recommendation_breakdown(quiz_data.get("recommendation", {}))
        render_reasoning_log(loop_data.get("reasoning", []), "Full Pipeline Log")
        st.caption("Slot 1 should be vid_003 (next in Interview Confidence).")
        knowledge_after = st.session_state.get(f"{PREFIX}_knowledge_after_quiz", {})
        render_knowledge_json(knowledge_after, "Final Knowledge State")

    step_nav(PREFIX, 8, 8, _set_step, invalidate_from=_INVALIDATE)
