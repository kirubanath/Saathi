import streamlit as st
import pandas as pd

from db.base import SessionLocal
from db.operations import get_video
from preprocessing.pipeline import preprocess_video, _resolve_transcript_path, SERIES_DIR
from storage.base import get_storage_client


def render_preprocessing(video_id: str):
    """Render preprocessing panel for a video. Runs the pipeline or shows existing artifacts."""

    db = SessionLocal()
    try:
        video = get_video(db, video_id)
        if not video:
            st.error(f"Video {video_id} not found in database.")
            return

        series_id = video.series_id
        category = video.category

        st.subheader(f"Preprocessing: {video.title}")
        st.caption(f"Video: {video_id} | Category: {category} | Series: {series_id}")

        # Check if already preprocessed
        storage = get_storage_client()
        already_done = storage.exists(f"videos/{video_id}/concept_profile.json")

        if already_done:
            st.success("Artifacts already exist in MinIO.")
            _display_existing_artifacts(video_id, storage)

            if st.button("Re-run Preprocessing", key=f"reprocess_{video_id}"):
                _run_pipeline(video_id, series_id, category)
        else:
            _run_pipeline(video_id, series_id, category)
    finally:
        db.close()


def _run_pipeline(video_id: str, series_id: str, category: str):
    """Execute the preprocessing pipeline with a spinner and display results."""
    transcript_path = _resolve_transcript_path(video_id, series_id)

    # Show transcript
    with st.expander("Transcript"):
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read()
        st.text(transcript[:2000] + ("..." if len(transcript) > 2000 else ""))
        st.caption(f"{len(transcript)} characters")

    with st.spinner("Running preprocessing pipeline (LLM calls in progress)..."):
        summary = preprocess_video(video_id, transcript_path, category)

    st.success("Preprocessing complete.")
    _display_summary(summary)

    # Show stored artifacts
    storage = get_storage_client()
    _display_existing_artifacts(video_id, storage)


def _display_summary(summary: dict):
    """Display preprocessing summary."""
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Concepts", len(summary.get("active_concepts", [])))
    col2.metric("Recaps Generated", summary.get("recap_count", 0))
    col3.metric("Question Sets", summary.get("question_count", 0))

    if summary.get("inactive_concepts"):
        st.caption(f"Inactive concepts (below 0.3 threshold): {', '.join(summary['inactive_concepts'])}")


def _display_existing_artifacts(video_id: str, storage):
    """Load and display artifacts from MinIO."""

    # Concept profile
    concept_profile = storage.get_json(f"videos/{video_id}/concept_profile.json")
    if concept_profile:
        with st.expander("Concept Profile", expanded=True):
            rows = []
            for concept, score in concept_profile.items():
                rows.append({
                    "Concept": concept.replace("_", " ").title(),
                    "Coverage": round(score, 2),
                    "Active": "Yes" if score >= 0.3 else "No",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Recap bullets
    recap_bullets = storage.get_json(f"videos/{video_id}/recap_bullets.json")
    if recap_bullets:
        with st.expander("Recap Bullets"):
            for concept, tones in recap_bullets.items():
                st.markdown(f"**{concept.replace('_', ' ').title()}**")
                if isinstance(tones, dict):
                    for tone, text in tones.items():
                        st.markdown(f"- *{tone.upper()}*: {text}")
                else:
                    st.markdown(f"- {tones}")

    # Questions
    questions = storage.get_json(f"videos/{video_id}/questions.json")
    if questions:
        with st.expander("Generated Questions"):
            for concept, difficulties in questions.items():
                st.markdown(f"**{concept.replace('_', ' ').title()}**")
                if isinstance(difficulties, dict):
                    for difficulty, q_data in difficulties.items():
                        st.markdown(f"- *{difficulty}*: {q_data.get('question', '')}")
                        if "options" in q_data:
                            for j, opt in enumerate(q_data["options"]):
                                marker = "(correct)" if j == q_data.get("correct_index") else ""
                                st.caption(f"  {j+1}. {opt} {marker}")

    # MinIO keys
    with st.expander("MinIO Storage Keys"):
        keys = [
            f"videos/{video_id}/concept_profile.json",
            f"videos/{video_id}/recap_bullets.json",
            f"videos/{video_id}/questions.json",
        ]
        for key in keys:
            exists = storage.exists(key)
            status = "Exists" if exists else "Missing"
            st.markdown(f"- `{key}` - {status}")
