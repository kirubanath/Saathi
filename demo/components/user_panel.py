"""Left-panel UI components.

Uses two card styles:
- learner_visible cards (blue + tag): recap, quiz, recs, progress — what
  the learner would actually see in production.
- event cards (neutral grey): profile, video watched — demo narrative
  context only, never shown in production.
"""

import streamlit as st
from demo.components.html_blocks import (
    panel_header_learner,
    user_profile_card,
    event_card,
    learner_visible_card,
    recap_card,
    quiz_result_card,
    recommendation_card,
    progress_card,
    journey_complete_banner,
)


def render_panel_header():
    panel_header_learner()


def render_user_profile(user_data: dict):
    """Event card: user profile (evaluator context)."""
    user_name = user_data.get("user_id", "").title()
    user_type = user_data.get("user_type", "")
    maturity = user_data.get("maturity", "").replace("_", " ").title()
    videos = user_data.get("total_videos_watched", 0)

    type_labels = {"AS": "Aspiration Seeker", "IS": "Information Seeker", "CO": "Converting"}
    type_display = type_labels.get(user_type, user_type)

    user_profile_card(user_name, type_display, maturity, videos)


def render_recap(bullets: list[dict]):
    """Learner-visible: recap bullets."""
    if not bullets:
        st.info("No recap generated for this path.")
        return

    for b in sorted(bullets, key=lambda x: x.get("rank", 0)):
        concept_label = b["concept"].replace("_", " ").title()
        recap_card(concept_label, b["bullet"], b.get("tone", ""))


def render_quiz(questions: list[dict], key_prefix: str):
    """Learner-visible: quiz questions. Returns answer indices when submitted."""
    if not questions:
        st.info("No quiz for this path.")
        return None

    for i, q in enumerate(questions):
        concept_label = q["concept"].replace("_", " ").title()
        learner_visible_card(f"Question {i+1}: {concept_label}", "")
        st.markdown(f"**{q['question']}**")
        st.radio(
            "Select answer",
            options=q["options"],
            key=f"{key_prefix}_q_{i}",
            label_visibility="collapsed",
        )

    if st.button("Submit Answers", key=f"{key_prefix}_submit", type="primary"):
        answers = []
        for i, q in enumerate(questions):
            selected = st.session_state.get(f"{key_prefix}_q_{i}")
            if selected is not None:
                answers.append(q["options"].index(selected))
            else:
                answers.append(0)
        return answers

    return None


def render_quiz_results(results: list[dict], questions: list[dict]):
    """Learner-visible: quiz results."""
    for i, (r, q) in enumerate(zip(results, questions)):
        concept_label = r["concept"].replace("_", " ").title()
        correct_answer = q["options"][q["correct_index"]]
        quiz_result_card(i + 1, concept_label, r["correct"], correct_answer)


def render_recommendation(recommendation: dict):
    """Learner-visible: recommendation cards."""
    if not recommendation:
        st.info("No recommendations generated.")
        return

    slot1 = recommendation.get("slot1")
    slot2 = recommendation.get("slot2")

    if slot1:
        title = slot1.get("title", slot1.get("video_id", "Unknown"))
        ctype = slot1.get("content_type", "")
        cat = slot1.get("category", "")
        ep = slot1.get("series_position", "?")
        recommendation_card("Next in Series", "series", title, f"{ctype} · {cat} · Episode {ep}")

    if slot2:
        title = slot2.get("title", slot2.get("video_id", "Unknown"))
        ctype = slot2.get("content_type", "")
        cat = slot2.get("category", "")
        ep = slot2.get("series_position", "?")
        recommendation_card("Engine Pick", "engine", title, f"{ctype} · {cat} · Episode {ep}")


def render_progress_message(message: str | None):
    """Learner-visible: progress update."""
    if message:
        progress_card(message)


def render_journey_complete(journey_name: str):
    journey_complete_banner(journey_name)
