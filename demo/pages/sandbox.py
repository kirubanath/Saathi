"""Sandbox: Free-form exploration page.

Any user + video combination, with optional fresh copy toggle.
Runs the full loop in one shot and displays all outputs.
"""

import copy
import os
import shutil
import tempfile

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import SessionLocal
from db.models import Video, User
from engine.loop import run_video_complete_loop, run_quiz_submit
from engine.quiz_engine import Question

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
    render_reasoning_log,
    render_quiz_difficulty,
)
from demo.components.state_display import render_knowledge_chart
from demo.pages.journey_core import _extract_user_data, _extract_loop_result, _extract_quiz_result


PREFIX = "sandbox"


def _get_db_session(use_fresh: bool):
    """Get a DB session, optionally from a fresh copy."""
    if use_fresh:
        if f"{PREFIX}_temp_db" not in st.session_state:
            temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
            os.close(temp_fd)
            seed_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saathi_seed.db")
            shutil.copy2(seed_path, temp_path)
            engine = create_engine(f"sqlite:///{temp_path}", connect_args={"check_same_thread": False})
            TempSession = sessionmaker(bind=engine)
            st.session_state[f"{PREFIX}_temp_db"] = temp_path
            st.session_state[f"{PREFIX}_temp_session_factory"] = TempSession
        return st.session_state[f"{PREFIX}_temp_session_factory"]()
    else:
        return SessionLocal()


def _cleanup_temp_db():
    """Remove temporary DB if it exists."""
    temp_path = st.session_state.pop(f"{PREFIX}_temp_db", None)
    st.session_state.pop(f"{PREFIX}_temp_session_factory", None)
    if temp_path and os.path.exists(temp_path):
        os.unlink(temp_path)


def render():
    st.title("Sandbox")
    st.caption("Run any user + video combination and see the full system output.")

    # Controls
    col1, col2, col3 = st.columns(3)

    with col1:
        # Load users from DB
        db = SessionLocal()
        try:
            users = db.query(User).all()
            user_options = {u.user_id: f"{u.user_id.title()} ({u.user_type}, {u.maturity})" for u in users}
        finally:
            db.close()

        selected_user = st.selectbox(
            "User",
            options=list(user_options.keys()),
            format_func=lambda x: user_options[x],
            key=f"{PREFIX}_user",
        )

    with col2:
        # Load videos from DB
        db = SessionLocal()
        try:
            videos = db.query(Video).order_by(Video.video_id).all()
            video_options = {
                v.video_id: f"{v.video_id}: {v.title} ({v.content_type})"
                for v in videos
            }
        finally:
            db.close()

        selected_video = st.selectbox(
            "Video",
            options=list(video_options.keys()),
            format_func=lambda x: video_options[x],
            key=f"{PREFIX}_video",
        )

    with col3:
        completion_rate = st.slider(
            "Completion Rate",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            key=f"{PREFIX}_completion",
        )

    use_fresh = st.toggle("Use fresh copy", value=True, key=f"{PREFIX}_fresh")

    if not use_fresh:
        st.warning("Running against live DB. State will be updated.")

    # Run button
    if st.button("Run", key=f"{PREFIX}_run", type="primary"):
        # Clear previous results
        for key in list(st.session_state.keys()):
            if key.startswith(f"{PREFIX}_result_"):
                del st.session_state[key]
        _cleanup_temp_db()

        db = _get_db_session(use_fresh)
        try:
            user = db.query(User).filter_by(user_id=selected_user).first()
            if not user:
                st.error(f"User {selected_user} not found.")
                return

            user_data = _extract_user_data(user)
            knowledge_before = copy.deepcopy(user.knowledge_state or {})

            result = run_video_complete_loop(db, selected_user, selected_video, completion_rate)
            loop_data = _extract_loop_result(result)

            db.refresh(user)
            knowledge_after_watch = copy.deepcopy(user.knowledge_state or {})

            st.session_state[f"{PREFIX}_result_user_data"] = user_data
            st.session_state[f"{PREFIX}_result_knowledge_before"] = knowledge_before
            st.session_state[f"{PREFIX}_result_loop_data"] = loop_data
            st.session_state[f"{PREFIX}_result_knowledge_after_watch"] = knowledge_after_watch
            st.session_state[f"{PREFIX}_result_has_quiz"] = loop_data.get("questions") is not None and len(loop_data.get("questions", [])) > 0
        finally:
            db.close()

    # Display results
    if f"{PREFIX}_result_loop_data" not in st.session_state:
        st.info("Select a user and video, then click Run.")
        return

    loop_data = st.session_state[f"{PREFIX}_result_loop_data"]
    user_data = st.session_state[f"{PREFIX}_result_user_data"]
    knowledge_before = st.session_state[f"{PREFIX}_result_knowledge_before"]

    st.markdown("---")

    # Two-column output
    left, right = st.columns(2)

    with left:
        st.header("User Experience")
        render_user_profile(user_data)

        # Recap
        if loop_data.get("recap"):
            render_recap(loop_data["recap"])
        else:
            st.info("No recap generated.")

        # Quiz
        if st.session_state.get(f"{PREFIX}_result_has_quiz"):
            questions = loop_data["questions"]

            # Check if quiz already submitted
            if f"{PREFIX}_result_quiz_data" in st.session_state:
                quiz_data = st.session_state[f"{PREFIX}_result_quiz_data"]
                render_quiz_results(quiz_data["eval_results"], questions)
                render_progress_message(quiz_data.get("progress_message"))
                render_recommendation(quiz_data.get("recommendation", {}))
            else:
                answers = render_quiz(questions, f"{PREFIX}_sq")
                if answers is not None:
                    # Submit quiz
                    q_objects = [
                        Question(
                            concept=q["concept"],
                            difficulty=q["difficulty"],
                            question=q["question"],
                            options=q["options"],
                            correct_index=q["correct_index"],
                        )
                        for q in questions
                    ]
                    db = _get_db_session(use_fresh)
                    try:
                        quiz_result = run_quiz_submit(db, selected_user, selected_video, q_objects, answers)
                        st.session_state[f"{PREFIX}_result_quiz_data"] = _extract_quiz_result(quiz_result)
                    finally:
                        db.close()
                    st.rerun()
        else:
            # No quiz path: show recommendation from loop result
            if loop_data.get("recommendation"):
                render_recommendation(loop_data["recommendation"])

    with right:
        st.header("System Reasoning")
        render_classification(loop_data["classification"])

        if loop_data.get("watch_update_delta"):
            render_watch_bump(loop_data["watch_update_delta"])

        if loop_data.get("recap"):
            from storage.base import get_storage_client
            concept_profile = None
            try:
                storage = get_storage_client()
                concept_profile = storage.get_json(f"videos/{selected_video}/concept_profile.json")
            except Exception:
                pass
            render_concept_ranking(loop_data["recap"], concept_profile)

        if st.session_state.get(f"{PREFIX}_result_has_quiz"):
            render_quiz_difficulty(loop_data.get("questions", []), knowledge_before)
            if f"{PREFIX}_result_quiz_data" in st.session_state:
                quiz_data = st.session_state[f"{PREFIX}_result_quiz_data"]
                render_knowledge_comparison(quiz_data["score_delta"])
                render_recommendation_breakdown(quiz_data.get("recommendation", {}))
        elif loop_data.get("recommendation"):
            render_recommendation_breakdown(loop_data["recommendation"])

        render_reasoning_log(loop_data.get("reasoning", []), "Full Reasoning Log")
