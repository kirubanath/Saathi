"""Preprocessing panel — shows LLM pipeline artifacts.

Uses html_blocks for system-style rendering (works inside st.tabs).
"""

import json
import streamlit as st

from db.base import SessionLocal
from db.operations import get_video
from preprocessing.pipeline import preprocess_video, _resolve_transcript_path, SERIES_DIR
from storage.base import get_storage_client

from demo.components.html_blocks import system_code_block


def render_preprocessing(video_id: str):
    """Render preprocessing panel for a video."""

    db = SessionLocal()
    try:
        video = get_video(db, video_id)
        if not video:
            st.error(f"Video {video_id} not found in database.")
            return

        series_id = video.series_id
        category = video.category

        system_code_block("Preprocessing Pipeline",
                          f"video_id: {video_id}\ntitle: {video.title}\n"
                          f"category: {category}\nseries: {series_id}")

        storage = get_storage_client()
        already_done = storage.exists(f"videos/{video_id}/concept_profile.json")

        if already_done:
            st.success("Artifacts exist in MinIO.")
            _display_existing_artifacts(video_id, storage)

            if st.button("Re-run Pipeline (LLM)", key=f"reprocess_{video_id}"):
                _run_pipeline(video_id, series_id, category)
        else:
            _run_pipeline(video_id, series_id, category)
    finally:
        db.close()


def _run_pipeline(video_id: str, series_id: str, category: str):
    """Execute the preprocessing pipeline — makes LLM calls."""
    transcript_path = _resolve_transcript_path(video_id, series_id)

    with st.expander("Transcript", expanded=False):
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read()
        st.code(transcript[:2000] + ("..." if len(transcript) > 2000 else ""), language="text")
        st.caption(f"{len(transcript)} characters")

    try:
        with st.spinner("Running preprocessing pipeline (LLM calls)..."):
            summary = preprocess_video(video_id, transcript_path, category)
    except Exception as e:
        st.error(f"Preprocessing failed: {e}")
        st.caption("Original artifacts (if any) are preserved in MinIO.")
        return

    st.success("Preprocessing complete.")
    _display_summary(summary)

    storage = get_storage_client()
    _display_existing_artifacts(video_id, storage)


def _display_summary(summary: dict):
    """Display preprocessing summary as metrics."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Concepts", len(summary.get("active_concepts", [])))
    c2.metric("Recaps", summary.get("recap_count", 0))
    c3.metric("Question Sets", summary.get("question_count", 0))

    if summary.get("inactive_concepts"):
        st.caption(f"Inactive (< 0.3): {', '.join(summary['inactive_concepts'])}")


def _display_existing_artifacts(video_id: str, storage):
    """Load and display artifacts from MinIO as code blocks."""

    concept_profile = storage.get_json(f"videos/{video_id}/concept_profile.json")
    if concept_profile:
        with st.expander("Concept Profile", expanded=True):
            st.code(json.dumps(concept_profile, indent=2), language="json")

    recap_bullets = storage.get_json(f"videos/{video_id}/recap_bullets.json")
    if recap_bullets:
        with st.expander("Recap Bullets"):
            st.code(json.dumps(recap_bullets, indent=2), language="json")

    questions = storage.get_json(f"videos/{video_id}/questions.json")
    if questions:
        with st.expander("Generated Questions"):
            st.code(json.dumps(questions, indent=2), language="json")

    with st.expander("MinIO Storage Keys"):
        keys = [
            f"videos/{video_id}/concept_profile.json",
            f"videos/{video_id}/recap_bullets.json",
            f"videos/{video_id}/questions.json",
        ]
        status_lines = []
        for key in keys:
            exists = storage.exists(key)
            status_lines.append(f"{'[OK]' if exists else '[  ]'} {key}")
        st.code("\n".join(status_lines), language="text")
