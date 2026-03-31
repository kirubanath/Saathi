"""State display components — knowledge charts and recall tables.

Shared between learner (visual chart) and system (JSON dump) panels.
"""

import streamlit as st
import pandas as pd

from demo.components.html_blocks import system_json_block


def render_knowledge_chart(knowledge_state: dict, title: str = "Knowledge State"):
    """Clean horizontal bar chart of concept scores."""
    if not knowledge_state:
        st.caption(f"*{title}: No data yet*")
        return

    rows = []
    for category, concepts in knowledge_state.items():
        for concept, score in concepts.items():
            label = concept.replace("_", " ").title()
            rows.append({
                "Concept": f"{label}",
                "Score": round(score, 3),
                "Category": category,
            })

    if not rows:
        st.caption(f"*{title}: No data yet*")
        return

    df = pd.DataFrame(rows).sort_values("Score", ascending=True)

    colors = []
    for s in df["Score"]:
        if s < 0.3:
            colors.append("#e74c3c")
        elif s < 0.6:
            colors.append("#f39c12")
        else:
            colors.append("#2ecc71")
    df["Color"] = colors

    import plotly.graph_objects as go

    fig = go.Figure(go.Bar(
        x=df["Score"].tolist(),
        y=df["Concept"].tolist(),
        orientation="h",
        marker_color=df["Color"].tolist(),
        text=[f"{s:.2f}" for s in df["Score"]],
        textposition="outside",
        textfont=dict(size=11),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13)),
        xaxis=dict(range=[0, 1.08], title="", showgrid=True,
                    gridcolor="rgba(128,128,128,0.08)"),
        yaxis=dict(title=""),
        height=max(180, len(rows) * 36 + 60),
        margin=dict(l=10, r=30, t=35, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig)


def render_knowledge_json(knowledge_state: dict, title: str = "Knowledge State"):
    """Dump raw knowledge state as JSON for the system panel."""
    if not knowledge_state:
        st.caption(f"*{title}: empty*")
        return

    system_json_block(title, knowledge_state)


def render_recall_timeline(recalls: list, title: str = "Recall Queue"):
    """Render recall entries as a clean data table."""
    if not recalls:
        st.caption(f"*{title}: No entries*")
        return

    rows = []
    for r in recalls:
        if hasattr(r, "concept_key"):
            rows.append({
                "Concept": r.concept_key,
                "Source": getattr(r, "source_video_id", ""),
                "Due": str(getattr(r, "due_at", "")),
                "Interval": f"{getattr(r, 'interval_hours', '')}h",
                "Status": getattr(r, "status", "pending"),
            })
        elif isinstance(r, dict):
            rows.append({
                "Concept": r.get("concept_key", ""),
                "Source": r.get("source_video_id", ""),
                "Due": str(r.get("due_at", "")),
                "Interval": f"{r.get('interval_hours', '')}h",
                "Status": r.get("status", "pending"),
            })

    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True)
