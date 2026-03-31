import streamlit as st
import pandas as pd


def render_classification(classification: dict):
    """Render classification decision cascade."""
    col1, col2, col3 = st.columns(3)
    col1.metric("Content Type", classification.get("content_type", ""))
    col2.metric("User Type", classification.get("user_type", ""))
    col3.metric("Maturity", classification.get("maturity", "").replace("_", " ").title())

    # Feature flags as a compact row
    flags_text = " | ".join([
        f"Recap: {'Yes' if classification.get('show_recap') else 'No'}",
        f"Quiz: {'Yes' if classification.get('show_quiz') else 'No'}",
        f"Recall: {'Yes' if classification.get('show_recall') else 'No'}",
        f"Max Bullets: {classification.get('max_bullets', 0)}",
        f"Difficulty Cap: {classification.get('difficulty_cap') or 'None'}",
    ])
    st.caption(flags_text)

    reasoning = classification.get("reasoning", [])
    if reasoning:
        with st.expander("Classification reasoning", expanded=False):
            for i, step in enumerate(reasoning, 1):
                st.markdown(f"{i}. {step}")


def render_concept_ranking(bullets: list[dict], concept_profile: dict | None = None):
    """Render concept ranking table from recap bullets."""
    if not bullets:
        return

    rows = []
    for b in sorted(bullets, key=lambda x: x.get("rank", 0)):
        rows.append({
            "Rank": b.get("rank", 0),
            "Concept": b["concept"].replace("_", " ").title(),
            "Coverage": f"{b.get('coverage_score', 0):.2f}",
            "Gap": f"{b.get('gap_score', 0):.2f}",
            "Tone": b.get("tone", ""),
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if concept_profile:
        with st.expander("Full concept profile"):
            profile_rows = []
            for concept, score in concept_profile.items():
                profile_rows.append({
                    "Concept": concept.replace("_", " ").title(),
                    "Coverage": f"{score:.2f}",
                    "Active": "Yes" if score >= 0.3 else "No",
                })
            st.dataframe(pd.DataFrame(profile_rows), use_container_width=True, hide_index=True)


def render_knowledge_comparison(delta: dict):
    """Render before/after knowledge state comparison."""
    if not delta:
        st.info("No knowledge changes.")
        return

    rows = []
    for concept, d in delta.items():
        before = d.get("before", 0)
        after = d.get("after", 0)
        change = after - before
        rows.append({
            "Concept": concept.replace("_", " ").title(),
            "Before": f"{before:.3f}",
            "After": f"{after:.3f}",
            "Delta": f"{change:+.3f}",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_watch_bump(watch_update_delta: dict):
    """Render watch bump details."""
    if not watch_update_delta:
        return

    render_knowledge_comparison(watch_update_delta)
    st.caption("Formula: new = min(0.8, old + 0.1 x completion_rate x coverage)")


def render_recommendation_breakdown(recommendation: dict):
    """Render recommendation reasoning."""
    if not recommendation:
        return

    reasoning = recommendation.get("reasoning", [])
    if reasoning:
        with st.expander("Recommendation reasoning", expanded=False):
            for i, step in enumerate(reasoning, 1):
                st.markdown(f"{i}. {step}")


def render_recall_details(recalls_scheduled: int, reasoning: list[str] | None = None):
    """Render recall scheduling information."""
    st.metric("Recalls Scheduled", recalls_scheduled)
    st.caption("Intervals: score < 0.4 = 18h, 0.4-0.6 = 30h, > 0.6 = 48h")

    if reasoning:
        with st.expander("Scheduling details"):
            for step in reasoning:
                st.markdown(f"- {step}")


def render_reasoning_log(reasoning: list[str], title: str = "System reasoning"):
    """Generic reasoning list renderer."""
    if not reasoning:
        return

    with st.expander(title, expanded=False):
        for i, step in enumerate(reasoning, 1):
            st.markdown(f"{i}. {step}")


def render_quiz_difficulty(questions: list[dict], knowledge_before: dict | None = None):
    """Show difficulty selection reasoning per question."""
    if not questions:
        return

    rows = []
    for q in questions:
        concept = q["concept"]
        score = "N/A"
        if knowledge_before:
            for cat_concepts in knowledge_before.values():
                if concept in cat_concepts:
                    score = f"{cat_concepts[concept]:.2f}"
                    break
        rows.append({
            "Concept": concept.replace("_", " ").title(),
            "Score": score,
            "Difficulty": q["difficulty"],
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("Rule: < 0.4 = easy, 0.4-0.7 = medium, > 0.7 = hard")
