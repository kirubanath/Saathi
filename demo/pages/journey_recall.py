"""Journey 4: Day 2 Recall (Priya)

Simulates 24 hours after Journey 1. Surfaces recall questions, processes answers,
adjusts intervals, and applies micro-updates to knowledge state.
"""

import copy
from datetime import datetime, timedelta, timezone

import streamlit as st

from db.base import SessionLocal
from db.models import RecallQueue
from db.operations import get_user
from engine.knowledge_updater import update_from_recall
from engine.recall_scheduler import get_pending_recalls, process_recall_result

from demo.components.user_panel import render_user_profile
from demo.components.system_panel import render_knowledge_comparison
from demo.components.state_display import render_knowledge_chart
from demo.pages.journey_core import _extract_user_data


USER_ID = "priya"
PREFIX = "j4"


def _get_step():
    return st.session_state.get(f"{PREFIX}_step", 0)


def _set_step(step):
    st.session_state[f"{PREFIX}_step"] = step


def render():
    st.title("Journey 4: Day 2 Recall")
    st.caption("Priya returns 24 hours after Journey 1. Time is simulated.")

    step = _get_step()

    if step == 0:
        _render_prestart()
    elif step == 1:
        _render_session_start()
    elif step == 2:
        _render_recall_quiz()
    elif step == 3:
        _render_complete()


def _render_prestart():
    st.markdown("**Simulating: 24 hours later.** No preprocessing needed for recall.")

    if "j1_completion_time" not in st.session_state:
        st.warning("Journey 1 not completed. Run Journey 1 first so recalls exist.")

    if st.button("Start Journey", key=f"{PREFIX}_start", type="primary"):
        _set_step(1)
        st.rerun()


def _render_session_start():
    st.markdown("### Session Start")

    j1_time = st.session_state.get("j1_completion_time", datetime.now(timezone.utc))
    simulated_time = j1_time + timedelta(hours=24)
    st.caption(f"Simulated time: {simulated_time.strftime('%Y-%m-%d %H:%M UTC')} (J1 + 24h)")

    if f"{PREFIX}_recalls" not in st.session_state:
        db = SessionLocal()
        try:
            user = get_user(db, USER_ID)
            st.session_state[f"{PREFIX}_user_data"] = _extract_user_data(user)
            st.session_state[f"{PREFIX}_knowledge_before"] = copy.deepcopy(user.knowledge_state)

            recalls = get_pending_recalls(db, USER_ID, simulated_time)
            st.session_state[f"{PREFIX}_recalls"] = [
                {
                    "recall_id": r.recall_id,
                    "concept_key": r.concept_key,
                    "source_video_id": r.source_video_id,
                    "question": r.question,
                    "due_at": str(r.due_at),
                    "interval_hours": r.interval_hours,
                }
                for r in recalls
            ]
        finally:
            db.close()

    recalls = st.session_state[f"{PREFIX}_recalls"]

    left, right = st.columns(2)
    with left:
        render_user_profile(st.session_state[f"{PREFIX}_user_data"])
        render_knowledge_chart(st.session_state[f"{PREFIX}_knowledge_before"], "Knowledge Before Recalls")
    with right:
        st.markdown("##### Pending Recalls")
        if recalls:
            st.metric("Due", len(recalls))
            for r in recalls:
                with st.container(border=True):
                    st.markdown(f"**{r['concept_key']}** (from {r['source_video_id']})")
                    st.caption(f"Interval: {r['interval_hours']}h")
        else:
            st.warning("No recalls due. Run Journey 1 first.")

    if recalls:
        if st.button("Next", key=f"{PREFIX}_to_step2", type="primary"):
            _set_step(2)
            st.rerun()


def _render_recall_quiz():
    st.markdown("### Answer Recalls")

    recalls = st.session_state[f"{PREFIX}_recalls"]
    if not recalls:
        st.info("No recalls to answer.")
        return

    left, right = st.columns(2)

    with left:
        for i, r in enumerate(recalls):
            question = r["question"]
            with st.container(border=True):
                st.markdown(f"**{r['concept_key']}**")
                st.markdown(question.get("question", ""))
                options = question.get("options", [])
                if options:
                    st.radio("Answer", options=options, key=f"{PREFIX}_recall_{i}", label_visibility="collapsed")

        submitted = st.button("Submit", key=f"{PREFIX}_recall_submit", type="primary")

    with right:
        st.markdown("##### Recall Rules")
        st.caption("Correct = double interval")
        st.caption("Incorrect = halve interval (min 12h)")
        st.caption("Knowledge update alpha = 0.15")

    if submitted:
        results = []
        db = SessionLocal()
        try:
            user = get_user(db, USER_ID)
            for i, r in enumerate(recalls):
                question = r["question"]
                options = question.get("options", [])
                selected = st.session_state.get(f"{PREFIX}_recall_{i}")
                answer_index = options.index(selected) if selected and options else 0
                correct = answer_index == question.get("correct_index", -1)

                recall_obj = db.get(RecallQueue, r["recall_id"])
                if recall_obj:
                    recall_update = process_recall_result(db, recall_obj, correct)
                    result_score = 1.0 if correct else 0.0
                    knowledge_update = update_from_recall(db, user, r["concept_key"], result_score)
                    db.refresh(user)
                    results.append({
                        "concept": r["concept_key"],
                        "correct": correct,
                        "new_interval": recall_update.new_interval,
                        "knowledge_delta": copy.deepcopy(knowledge_update.delta),
                    })

            st.session_state[f"{PREFIX}_recall_results"] = results
            st.session_state[f"{PREFIX}_knowledge_after"] = copy.deepcopy(user.knowledge_state)
        finally:
            db.close()

        _set_step(3)
        st.rerun()


def _render_complete():
    st.markdown("### Results")

    results = st.session_state.get(f"{PREFIX}_recall_results", [])

    left, right = st.columns(2)

    with left:
        for r in results:
            with st.container(border=True):
                if r["correct"]:
                    st.success(f"{r['concept']}: Correct")
                else:
                    st.error(f"{r['concept']}: Incorrect")
                st.caption(f"New interval: {r['new_interval']:.1f}h")

        st.success("Journey 4 Complete")

    with right:
        for r in results:
            if r.get("knowledge_delta"):
                render_knowledge_comparison(r["knowledge_delta"])

        knowledge_after = st.session_state.get(f"{PREFIX}_knowledge_after", {})
        render_knowledge_chart(knowledge_after, "Final Knowledge State")
