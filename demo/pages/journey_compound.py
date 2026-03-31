"""Journey 3: Loop Compounds (Priya + vid_002)

Same flow as Journey 1 but with vid_002 and post-Journey-1 knowledge state.
"""

import copy

import streamlit as st

from db.base import SessionLocal
from db.operations import get_user
from engine.loop import run_video_complete_loop, run_quiz_submit
from engine.quiz_engine import Question
from storage.base import get_storage_client

from demo.components.preprocessing_panel import render_preprocessing
from demo.components.user_panel import (
    render_user_profile, render_recap, render_quiz, render_quiz_results,
    render_recommendation, render_progress_message,
)
from demo.components.system_panel import (
    render_classification, render_concept_ranking, render_knowledge_comparison,
    render_watch_bump, render_recommendation_breakdown, render_reasoning_log,
    render_quiz_difficulty,
)
from demo.components.state_display import render_knowledge_chart
from demo.pages.journey_core import _extract_user_data, _extract_loop_result, _extract_quiz_result


USER_ID = "priya"
VIDEO_ID = "vid_002"
PREFIX = "j3"


def _get_step():
    return st.session_state.get(f"{PREFIX}_step", 0)


def _set_step(step):
    st.session_state[f"{PREFIX}_step"] = step


def render():
    st.title("Journey 3: Loop Compounds")
    st.caption("Priya watches vid_002 (Interview Confidence Ep 2) with post-Journey-1 knowledge")

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
        _render_quiz()
    elif step == 5:
        _render_quiz_submit()
    elif step == 6:
        _render_knowledge_update()
    elif step == 7:
        _render_recommendation()


def _render_prestart():
    st.markdown("Priya watches the Slot 1 pick from Journey 1. Her knowledge has shifted, so concept targeting and difficulty adapt.")

    if "j1_step" not in st.session_state or st.session_state.get("j1_step", 0) < 8:
        st.warning("Journey 1 not completed. Run Journey 1 first for the compounding effect.")

    col1, col2, _ = st.columns([1, 1, 2])
    with col1:
        if st.button("Preprocess vid_002", key=f"{PREFIX}_preprocess"):
            st.session_state[f"{PREFIX}_show_preprocess"] = True
    with col2:
        if st.button("Start Journey", key=f"{PREFIX}_start", type="primary"):
            _set_step(1)
            st.rerun()

    if st.session_state.get(f"{PREFIX}_show_preprocess"):
        render_preprocessing(VIDEO_ID)


def _render_profile():
    st.markdown("### User Profile (Post-Journey 1)")

    if f"{PREFIX}_user_data" not in st.session_state:
        db = SessionLocal()
        try:
            user = get_user(db, USER_ID)
            user_data = _extract_user_data(user)
            st.session_state[f"{PREFIX}_user_data"] = user_data
            st.session_state[f"{PREFIX}_knowledge_before"] = copy.deepcopy(user_data["knowledge_state"])
        finally:
            db.close()

    user_data = st.session_state[f"{PREFIX}_user_data"]

    left, right = st.columns(2)
    with left:
        render_user_profile(user_data)
        j1_before = st.session_state.get("j1_knowledge_before", {})
        if j1_before:
            st.caption("Changes since Journey 1 start:")
            for cat, concepts in user_data["knowledge_state"].items():
                for concept, score in concepts.items():
                    j1_score = j1_before.get(cat, {}).get(concept, 0)
                    if score != j1_score:
                        st.caption(f"  {concept}: {j1_score:.3f} -> {score:.3f}")
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
            user = get_user(db, USER_ID)
            st.session_state[f"{PREFIX}_knowledge_after_watch"] = copy.deepcopy(user.knowledge_state)
        finally:
            db.close()

    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = st.columns(2)
    with left:
        st.markdown(f"Priya watched **Interview Confidence Ep 2** (`{VIDEO_ID}`)")
        if loop_data.get("watch_update_delta"):
            render_watch_bump(loop_data["watch_update_delta"])
    with right:
        render_classification(loop_data["classification"])

    if st.button("Next", key=f"{PREFIX}_to_step3", type="primary"):
        _set_step(3)
        st.rerun()


def _render_recap():
    st.markdown("### Personalized Recap")

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
    with right:
        render_concept_ranking(recap_bullets or [], concept_profile)
        render_reasoning_log(loop_data.get("recap_reasoning", []), "Recap reasoning")

    if st.button("Next", key=f"{PREFIX}_to_step4", type="primary"):
        _set_step(4)
        st.rerun()


def _render_quiz():
    st.markdown("### Quiz")

    loop_data = st.session_state[f"{PREFIX}_loop_data"]
    questions = loop_data.get("questions", [])
    knowledge_before = st.session_state.get(f"{PREFIX}_knowledge_before", {})

    left, right = st.columns(2)
    with left:
        answers = render_quiz(questions, PREFIX)
        if answers is not None:
            st.session_state[f"{PREFIX}_answers"] = answers
            _set_step(5)
            st.rerun()
    with right:
        st.markdown("##### Difficulty Selection")
        render_quiz_difficulty(questions, knowledge_before)
        st.caption("Difficulty may be higher for concepts that improved in Journey 1.")


def _render_quiz_submit():
    st.markdown("### Evaluation")

    if f"{PREFIX}_quiz_data" not in st.session_state:
        loop_data = st.session_state[f"{PREFIX}_loop_data"]
        answers = st.session_state[f"{PREFIX}_answers"]

        questions = [
            Question(
                concept=q["concept"], difficulty=q["difficulty"],
                question=q["question"], options=q["options"], correct_index=q["correct_index"],
            )
            for q in loop_data["questions"]
        ]

        db = SessionLocal()
        try:
            result = run_quiz_submit(db, USER_ID, VIDEO_ID, questions, answers)
            st.session_state[f"{PREFIX}_quiz_data"] = _extract_quiz_result(result)
            user = get_user(db, USER_ID)
            st.session_state[f"{PREFIX}_knowledge_after_quiz"] = copy.deepcopy(user.knowledge_state)
        finally:
            db.close()

    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]
    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = st.columns(2)
    with left:
        render_quiz_results(quiz_data["eval_results"], loop_data["questions"])
    with right:
        correct_count = sum(1 for r in quiz_data["eval_results"] if r["correct"])
        st.metric("Score", f"{correct_count}/{len(quiz_data['eval_results'])}")

    if st.button("Next", key=f"{PREFIX}_to_step6", type="primary"):
        _set_step(6)
        st.rerun()


def _render_knowledge_update():
    st.markdown("### Knowledge Update")

    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]

    left, right = st.columns(2)
    with left:
        render_progress_message(quiz_data.get("progress_message"))
    with right:
        render_knowledge_comparison(quiz_data["score_delta"])

    if st.button("Next", key=f"{PREFIX}_to_step7", type="primary"):
        _set_step(7)
        st.rerun()


def _render_recommendation():
    st.markdown("### Recommendations")

    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]

    left, right = st.columns(2)
    with left:
        render_recommendation(quiz_data.get("recommendation", {}))
        st.success("Journey 3 Complete")
    with right:
        render_recommendation_breakdown(quiz_data.get("recommendation", {}))
        st.caption("Slot 1 should be vid_003 (next in Interview Confidence).")
        knowledge_after = st.session_state.get(f"{PREFIX}_knowledge_after_quiz", {})
        render_knowledge_chart(knowledge_after, "Final Knowledge State")
