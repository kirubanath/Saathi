"""Journey 1: Core Loop (Priya + vid_001)

Full AS path: video complete -> classification -> recap -> quiz -> evaluation ->
knowledge update -> progress message -> recommendation -> recall scheduling.
"""

import copy
from datetime import datetime, timezone

import streamlit as st

from db.base import SessionLocal
from db.operations import get_user, get_video
from engine.loop import run_video_complete_loop, run_quiz_submit
from engine.quiz_engine import Question
from storage.base import get_storage_client

from demo.components.preprocessing_panel import render_preprocessing
from demo.components.user_panel import (
    render_user_profile,
    render_recap,
    render_quiz,
    render_quiz_results,
    render_recommendation,
    render_progress_message,
)
from demo.components.system_panel import (
    render_classification,
    render_concept_ranking,
    render_knowledge_comparison,
    render_watch_bump,
    render_recommendation_breakdown,
    render_recall_details,
    render_reasoning_log,
    render_quiz_difficulty,
)
from demo.components.state_display import render_knowledge_chart


USER_ID = "priya"
VIDEO_ID = "vid_001"
PREFIX = "j1"


def _get_step():
    return st.session_state.get(f"{PREFIX}_step", 0)


def _set_step(step):
    st.session_state[f"{PREFIX}_step"] = step


def _extract_user_data(user):
    """Extract serializable user data from ORM object."""
    return {
        "user_id": user.user_id,
        "user_type": user.user_type,
        "maturity": user.maturity,
        "total_videos_watched": user.total_videos_watched,
        "knowledge_state": copy.deepcopy(user.knowledge_state) if user.knowledge_state else {},
    }


def _extract_loop_result(result):
    """Convert LoopResult to a serializable dict for session state storage."""
    data = {
        "classification": {
            "content_type": result.classification.content_type,
            "user_type": result.classification.user_type,
            "maturity": result.classification.maturity,
            "show_recap": result.classification.show_recap,
            "show_quiz": result.classification.show_quiz,
            "show_recall": result.classification.show_recall,
            "max_bullets": result.classification.max_bullets,
            "difficulty_cap": result.classification.difficulty_cap,
            "reasoning": list(result.classification.reasoning),
        },
        "recap": None,
        "questions": None,
        "recommendation": None,
        "watch_update_delta": None,
        "reasoning": list(result.reasoning),
    }

    if result.recap:
        data["recap"] = [
            {
                "concept": b.concept,
                "bullet": b.bullet,
                "tone": b.tone,
                "coverage_score": b.coverage_score,
                "gap_score": b.gap_score,
                "rank": b.rank,
            }
            for b in result.recap.bullets
        ]
        data["recap_reasoning"] = list(result.recap.reasoning)

    if result.questions:
        data["questions"] = [
            {
                "concept": q.concept,
                "difficulty": q.difficulty,
                "question": q.question,
                "options": list(q.options),
                "correct_index": q.correct_index,
            }
            for q in result.questions
        ]

    if result.recommendation:
        data["recommendation"] = {
            "slot1": result.recommendation.slot1,
            "slot2": result.recommendation.slot2,
            "reasoning": list(result.recommendation.reasoning),
        }

    if result.watch_update:
        data["watch_update_delta"] = copy.deepcopy(result.watch_update.delta)

    return data


def _extract_quiz_result(result):
    """Convert QuizResult to a serializable dict."""
    data = {
        "eval_results": [
            {"concept": r.concept, "correct": r.correct, "score": r.score}
            for r in result.eval_results
        ],
        "score_delta": copy.deepcopy(result.score_delta),
        "progress_message": result.progress_message,
        "recommendation": {
            "slot1": result.recommendation.slot1,
            "slot2": result.recommendation.slot2,
            "reasoning": list(result.recommendation.reasoning),
        } if result.recommendation else None,
        "recalls_scheduled": result.recalls_scheduled,
        "reasoning": list(result.reasoning),
    }
    return data


STEP_LABELS = [
    "Pre-start", "Profile", "Video Complete", "Recap",
    "Quiz", "Evaluation", "Knowledge Update", "Recommendations", "Recall",
]


def _render_step_indicator(current: int):
    """Render a compact step progress bar."""
    if current == 0:
        return
    cols = st.columns(len(STEP_LABELS) - 1)
    for i, (col, label) in enumerate(zip(cols, STEP_LABELS[1:])):
        step_num = i + 1
        if step_num < current:
            col.markdown(f"<div style='text-align:center;color:#2ecc71;font-size:0.75rem'>&#10003; {label}</div>", unsafe_allow_html=True)
        elif step_num == current:
            col.markdown(f"<div style='text-align:center;color:#4A90D9;font-weight:600;font-size:0.75rem'>{label}</div>", unsafe_allow_html=True)
        else:
            col.markdown(f"<div style='text-align:center;color:#ccc;font-size:0.75rem'>{label}</div>", unsafe_allow_html=True)
    st.markdown("")


def render():
    st.title("Journey 1: Core Loop")
    st.caption("Priya (AS, Warming Up) watches vid_001 (Interview Confidence Ep 1)")

    step = _get_step()
    _render_step_indicator(step)

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
    elif step == 8:
        _render_recall()


def _render_prestart():
    st.markdown(
        "Full learning loop: classify, recap, quiz, knowledge update, recommend, schedule recall."
    )

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
            user_data = _extract_user_data(user)
            st.session_state[f"{PREFIX}_user_data"] = user_data
            st.session_state[f"{PREFIX}_knowledge_before"] = copy.deepcopy(user_data["knowledge_state"])
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
            user = get_user(db, USER_ID)
            st.session_state[f"{PREFIX}_knowledge_after_watch"] = copy.deepcopy(user.knowledge_state)
        finally:
            db.close()

    loop_data = st.session_state[f"{PREFIX}_loop_data"]

    left, right = st.columns(2)
    with left:
        st.markdown(f"Priya watched **Interview Confidence Ep 1** (`{VIDEO_ID}`)")
        if loop_data.get("watch_update_delta"):
            st.markdown("##### Watch Bump")
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


def _render_quiz_submit():
    st.markdown("### Evaluation")

    if f"{PREFIX}_quiz_data" not in st.session_state:
        loop_data = st.session_state[f"{PREFIX}_loop_data"]
        questions_data = loop_data["questions"]
        answers = st.session_state[f"{PREFIX}_answers"]

        questions = [
            Question(
                concept=q["concept"],
                difficulty=q["difficulty"],
                question=q["question"],
                options=q["options"],
                correct_index=q["correct_index"],
            )
            for q in questions_data
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
        total = len(quiz_data["eval_results"])
        st.metric("Score", f"{correct_count}/{total}")
        render_reasoning_log(quiz_data["reasoning"], "Evaluation reasoning")

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
        st.caption("EMA: new = old + 0.3 x (score - old)")

    if st.button("Next", key=f"{PREFIX}_to_step7", type="primary"):
        _set_step(7)
        st.rerun()


def _render_recommendation():
    st.markdown("### Recommendations")

    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]

    left, right = st.columns(2)
    with left:
        render_recommendation(quiz_data.get("recommendation", {}))
    with right:
        render_recommendation_breakdown(quiz_data.get("recommendation", {}))

    if st.button("Next", key=f"{PREFIX}_to_step8", type="primary"):
        _set_step(8)
        st.rerun()


def _render_recall():
    st.markdown("### Recall Scheduling")

    quiz_data = st.session_state[f"{PREFIX}_quiz_data"]

    if f"{PREFIX}_completion_time" not in st.session_state:
        st.session_state[f"{PREFIX}_completion_time"] = datetime.now(timezone.utc)

    left, right = st.columns(2)
    with left:
        st.success("Journey 1 Complete")
        knowledge_after = st.session_state.get(f"{PREFIX}_knowledge_after_quiz", {})
        render_knowledge_chart(knowledge_after, "Final Knowledge State")
    with right:
        render_recall_details(quiz_data["recalls_scheduled"])
        st.caption("Journey 4 will simulate 24h later to surface these recalls.")
