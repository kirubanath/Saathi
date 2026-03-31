"""Journey 4: Day 2 Recall (Priya)

Simulates 48 hours after Journey 1. Surfaces recall questions, processes answers,
adjusts intervals, and applies micro-updates to knowledge state.

All data flows through the FastAPI server over HTTP.
"""

import copy
from datetime import datetime, timedelta, timezone

import streamlit as st

from demo import api_client

from demo.components.html_blocks import (
    learner_visible_card, journey_prestart_card, step_nav,
    system_code_block, system_json_block, step_columns,
)
from demo.components.user_panel import (
    render_panel_header as render_learner_header,
    render_user_profile,
    render_journey_complete,
)
from demo.components.system_panel import (
    render_panel_header as render_system_header,
    render_knowledge_comparison,
)
from demo.components.state_display import render_knowledge_chart, render_knowledge_json


USER_ID = "priya"
PREFIX = "j4"

_INVALIDATE = {
    3: [f"{PREFIX}_recall_results", f"{PREFIX}_knowledge_after"],
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

    if step == 1:
        _render_session_start()
    elif step == 2:
        _render_recall_quiz()
    elif step == 3:
        _render_complete()


def _render_prestart():
    journey_prestart_card(
        "Journey 4: Day 2 Recall",
        "Simulating 48 hours later. Priya returns and the system checks "
        "her recall queue. All scheduled recalls are now due.",
        "User: Priya · Trigger: Session start with pending recalls",
    )

    if "j1_completion_time" not in st.session_state:
        st.warning("Journey 1 not completed. Run Journey 1 first so recalls exist.")

    if st.button("Start Journey", key=f"{PREFIX}_start", type="primary"):
        _set_step(1)
        st.rerun()


def _render_session_start():
    j1_time = st.session_state.get("j1_completion_time", datetime.now(timezone.utc))
    simulated_time = j1_time + timedelta(hours=48)

    if f"{PREFIX}_recalls" not in st.session_state:
        try:
            session_data = api_client.session_start(USER_ID, simulated_time.isoformat())
        except Exception as e:
            st.error(f"Could not reach API server: {e}")
            return
        st.session_state[f"{PREFIX}_user_data"] = session_data["user_data"]
        st.session_state[f"{PREFIX}_knowledge_before"] = copy.deepcopy(session_data["knowledge_before"])
        st.session_state[f"{PREFIX}_recalls"] = session_data["recalls"]

    recalls = st.session_state[f"{PREFIX}_recalls"]

    left, right = step_columns("j4_s1")
    with left:
        render_learner_header()
        render_user_profile(st.session_state[f"{PREFIX}_user_data"])
        if recalls:
            count = len(recalls)
            learner_visible_card("Recall Check",
                               f"{count} review question{'s' if count != 1 else ''} "
                               "surfaced from previous sessions.")
        else:
            st.info("No reviews due right now.")

    with right:
        render_system_header()
        sim_str = simulated_time.strftime('%Y-%m-%d %H:%M UTC')

        recall_data = [
            {"concept": r["concept_key"], "source": r["source_video_id"],
             "interval": f"{r['interval_hours']}h", "due_at": r["due_at"]}
            for r in recalls
        ]

        system_json_block("Recall Queue Check", {
            "simulated_time": sim_str,
            "pending_recalls": len(recalls),
            "entries": recall_data,
        })

        render_knowledge_json(
            st.session_state[f"{PREFIX}_knowledge_before"],
            "Knowledge Before Recalls",
        )

    step_nav(PREFIX, 1, 3, _set_step, show_next=bool(recalls))


def _render_recall_quiz():
    recalls = st.session_state[f"{PREFIX}_recalls"]
    if not recalls:
        st.info("No recalls to answer.")
        return

    left, right = step_columns("j4_s2")

    with left:
        render_learner_header()
        st.markdown("**Recall questions — spaced repetition check:**")
        for i, r in enumerate(recalls):
            question = r["question"]
            concept_label = r["concept_key"].replace("_", " ").title()
            learner_visible_card(f"Review: {concept_label}", "")
            st.markdown(f"**{question.get('question', '')}**")
            options = question.get("options", [])
            if options:
                st.radio("Answer", options=options, key=f"{PREFIX}_recall_{i}", label_visibility="collapsed")

        submitted = st.button("Submit", key=f"{PREFIX}_recall_submit", type="primary")

    with right:
        render_system_header()
        system_json_block("Recall Rules", {
            "correct": {
                "interval": "interval × 2",
                "knowledge": "α = 0.15 (positive shift)",
            },
            "incorrect": {
                "interval": "max(12h, interval / 2)",
                "knowledge": "α = 0.15 (negative shift)",
            },
            "missed": "no penalty — reschedule at same interval",
        })

    step_nav(PREFIX, 2, 3, _set_step, show_next=False)

    if submitted:
        try:
            results = []
            for i, r in enumerate(recalls):
                question = r["question"]
                options = question.get("options", [])
                selected = st.session_state.get(f"{PREFIX}_recall_{i}")
                answer_index = options.index(selected) if selected and options else 0

                resp = api_client.recall_answer(USER_ID, r["recall_id"], answer_index)
                results.append({
                    "concept": r["concept_key"],
                    "correct": resp["correct"],
                    "new_interval": resp["next_interval_hours"],
                    "knowledge_delta": resp.get("knowledge_delta", {}),
                })

            st.session_state[f"{PREFIX}_recall_results"] = results
            last_resp = api_client.get_user(USER_ID)
            st.session_state[f"{PREFIX}_knowledge_after"] = copy.deepcopy(last_resp["knowledge_state"])
        except Exception as e:
            st.error(f"API error during recall processing: {e}")
            return

        _set_step(3)
        st.rerun()


def _render_complete():
    results = st.session_state.get(f"{PREFIX}_recall_results", [])

    left, right = step_columns("j4_s3")

    with left:
        render_learner_header()
        for r in results:
            concept_label = r["concept"].replace("_", " ").title()
            if r["correct"]:
                learner_visible_card(f"✓ {concept_label}",
                                     f"Correct — next review scheduled in {r['new_interval']:.0f}h.")
            else:
                learner_visible_card(f"✗ {concept_label}",
                                     f"Incorrect — review rescheduled in {r['new_interval']:.0f}h.")

        render_journey_complete("Day 2 Recall — Priya")

    with right:
        render_system_header()
        for r in results:
            if r.get("knowledge_delta"):
                render_knowledge_comparison(r["knowledge_delta"])

        recall_summary = [
            {"concept": r["concept"], "correct": r["correct"],
             "new_interval_hours": round(r["new_interval"], 1)}
            for r in results
        ]
        system_json_block("Recall Results", recall_summary)

        knowledge_after = st.session_state.get(f"{PREFIX}_knowledge_after", {})
        render_knowledge_json(knowledge_after, "Final Knowledge State")

    step_nav(PREFIX, 3, 3, _set_step, invalidate_from=_INVALIDATE)
