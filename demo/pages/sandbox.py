"""Sandbox: Free-form exploration page.

Any user + video combination. Runs the full loop in one shot via the API
and displays all outputs. Uses the live database — click Reset Demo to
restore seed state after experimenting.
"""

import copy

import streamlit as st

from demo import api_client
from demo.components.html_blocks import step_columns

from demo.components.user_panel import (
    render_panel_header as render_learner_header,
    render_user_profile,
    render_recap,
    render_quiz,
    render_quiz_results,
    render_recommendation,
    render_progress_message,
)
from demo.components.system_panel import (
    render_panel_header as render_system_header,
    render_classification,
    render_concept_ranking,
    render_knowledge_comparison,
    render_watch_bump,
    render_recommendation_breakdown,
    render_reasoning_log,
    render_quiz_difficulty,
)
from demo.components.state_display import render_knowledge_chart, render_knowledge_json


PREFIX = "sandbox"


def render():
    st.markdown("#### Sandbox")
    st.caption("Run any user + video combination. Full pipeline, one shot. Uses the live database — click Reset Demo to restore seed state.")

    try:
        users = api_client.list_users()
        videos = api_client.list_videos()
    except Exception as e:
        st.error(f"Could not reach FastAPI server: {e}")
        return

    user_options = {u["user_id"]: f"{u['user_id'].title()} ({u['user_type']}, {u['maturity']})" for u in users}
    video_options = {v["video_id"]: f"{v['video_id']}: {v['title']} ({v['content_type']})" for v in videos}

    c1, c2, c3 = st.columns([2, 3, 2])

    with c1:
        selected_user = st.selectbox(
            "User",
            options=list(user_options.keys()),
            format_func=lambda x: user_options[x],
            key=f"{PREFIX}_user",
        )

    with c2:
        selected_video = st.selectbox(
            "Video",
            options=list(video_options.keys()),
            format_func=lambda x: video_options[x],
            key=f"{PREFIX}_video",
        )

    with c3:
        completion_rate = st.slider(
            "Completion",
            min_value=0.0, max_value=1.0, value=1.0, step=0.05,
            key=f"{PREFIX}_completion",
        )

    if st.button("Run Pipeline", key=f"{PREFIX}_run", type="primary"):
        for key in list(st.session_state.keys()):
            if key.startswith(f"{PREFIX}_result_"):
                del st.session_state[key]

        try:
            user_data = api_client.get_user(selected_user)
            knowledge_before = copy.deepcopy(user_data.get("knowledge_state", {}))

            loop_data = api_client.video_complete(selected_user, selected_video, completion_rate)

            st.session_state[f"{PREFIX}_result_user_data"] = user_data
            st.session_state[f"{PREFIX}_result_knowledge_before"] = knowledge_before
            st.session_state[f"{PREFIX}_result_loop_data"] = loop_data
            st.session_state[f"{PREFIX}_result_has_quiz"] = bool(loop_data.get("questions"))
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            return

    if f"{PREFIX}_result_loop_data" not in st.session_state:
        st.markdown("---")
        st.caption("Select a user and video, then click **Run Pipeline**.")
        return

    loop_data = st.session_state[f"{PREFIX}_result_loop_data"]
    user_data = st.session_state[f"{PREFIX}_result_user_data"]
    knowledge_before = st.session_state[f"{PREFIX}_result_knowledge_before"]

    st.markdown("---")

    left, right = step_columns("sandbox")

    with left:
        render_learner_header()
        render_user_profile(user_data)

        if loop_data.get("recap"):
            st.markdown("**Recap:**")
            render_recap(loop_data["recap"])
        else:
            st.caption("*No recap generated (content type gate).*")

        if st.session_state.get(f"{PREFIX}_result_has_quiz"):
            questions = loop_data["questions"]

            if f"{PREFIX}_result_quiz_data" in st.session_state:
                quiz_data = st.session_state[f"{PREFIX}_result_quiz_data"]
                render_quiz_results(quiz_data["results"], questions)
                render_progress_message(quiz_data.get("progress_message"))
                render_recommendation(quiz_data.get("recommendation", {}))
            else:
                st.markdown("**Quiz:**")
                answers = render_quiz(questions, f"{PREFIX}_sq")
                if answers is not None:
                    answer_items = [
                        {"concept": q["concept"], "answer_index": a}
                        for q, a in zip(questions, answers)
                    ]
                    try:
                        quiz_data = api_client.quiz_submit(
                            selected_user, selected_video, questions, answer_items
                        )
                        st.session_state[f"{PREFIX}_result_quiz_data"] = quiz_data
                    except Exception as e:
                        st.error(f"Quiz submit error: {e}")
                    st.rerun()
        else:
            if loop_data.get("recommendation"):
                st.markdown("**Recommendations:**")
                render_recommendation(loop_data["recommendation"])

    with right:
        render_system_header()
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
                render_knowledge_comparison(quiz_data["progress"])
                render_recommendation_breakdown(quiz_data.get("recommendation", {}))
        elif loop_data.get("recommendation"):
            render_recommendation_breakdown(loop_data["recommendation"])

        render_reasoning_log(loop_data.get("reasoning", []), "Full Pipeline Log")
