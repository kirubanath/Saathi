import streamlit as st


def render_user_profile(user_data: dict):
    """Show user profile card."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("User", user_data.get("user_id", "").title())
    col2.metric("Type", user_data.get("user_type", ""))
    col3.metric("Maturity", user_data.get("maturity", "").replace("_", " ").title())
    col4.metric("Videos Watched", user_data.get("total_videos_watched", 0))


def render_recap(bullets: list[dict]):
    """Render recap bullets."""
    if not bullets:
        st.info("No recap generated for this path.")
        return

    for b in sorted(bullets, key=lambda x: x.get("rank", 0)):
        concept_label = b["concept"].replace("_", " ").title()
        with st.container(border=True):
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**{concept_label}**")
                st.markdown(b["bullet"])
            with cols[1]:
                st.caption(f"Tone: {b['tone'].upper()}")
                st.caption(f"Coverage: {b['coverage_score']:.2f}")
                st.caption(f"Gap: {b['gap_score']:.2f}")


def render_quiz(questions: list[dict], key_prefix: str):
    """Render quiz. Returns list of answer indices when submitted, None otherwise."""
    if not questions:
        st.info("No quiz for this path.")
        return None

    for i, q in enumerate(questions):
        concept_label = q["concept"].replace("_", " ").title()
        with st.container(border=True):
            st.markdown(f"**Q{i+1}** | {concept_label} | Difficulty: `{q['difficulty']}`")
            st.markdown(q["question"])
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
    """Show correct/incorrect per question."""
    for i, (r, q) in enumerate(zip(results, questions)):
        concept_label = r["concept"].replace("_", " ").title()
        correct_answer = q["options"][q["correct_index"]]
        if r["correct"]:
            st.success(f"Q{i+1} ({concept_label}): Correct")
        else:
            st.error(f"Q{i+1} ({concept_label}): Incorrect. Answer: {correct_answer}")


def render_recommendation(recommendation: dict):
    """Render recommendation cards."""
    if not recommendation:
        st.info("No recommendations generated.")
        return

    col1, col2 = st.columns(2)

    with col1:
        slot1 = recommendation.get("slot1")
        with st.container(border=True):
            st.caption("SLOT 1: NEXT IN SERIES")
            if slot1:
                st.markdown(f"**{slot1.get('title', slot1.get('video_id', 'Unknown'))}**")
                st.caption(f"{slot1.get('content_type', '')} / {slot1.get('category', '')}")
                st.caption(f"Episode {slot1.get('series_position', '?')}")
            else:
                st.markdown("*No series continuation*")

    with col2:
        slot2 = recommendation.get("slot2")
        with st.container(border=True):
            st.caption("SLOT 2: RECOMMENDED FOR YOU")
            if slot2:
                st.markdown(f"**{slot2.get('title', slot2.get('video_id', 'Unknown'))}**")
                st.caption(f"{slot2.get('content_type', '')} / {slot2.get('category', '')}")
                st.caption(f"Episode {slot2.get('series_position', '?')}")
            else:
                st.markdown("*No additional recommendation*")


def render_progress_message(message: str | None):
    """Display progress message."""
    if message:
        st.success(message)
