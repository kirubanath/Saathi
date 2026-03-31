import streamlit as st
import pandas as pd


def render_knowledge_chart(knowledge_state: dict, title: str = "Knowledge State"):
    """Render a horizontal bar chart of concept scores, grouped by category."""
    st.subheader(title)

    if not knowledge_state:
        st.info("No knowledge state yet.")
        return

    rows = []
    for category, concepts in knowledge_state.items():
        for concept, score in concepts.items():
            label = concept.replace("_", " ").title()
            rows.append({
                "Concept": f"{label} ({category})",
                "Score": round(score, 3),
                "Category": category,
            })

    if not rows:
        st.info("No knowledge state yet.")
        return

    df = pd.DataFrame(rows)
    df = df.sort_values("Score", ascending=True)

    # Color-code bars by score range
    colors = []
    for s in df["Score"]:
        if s < 0.3:
            colors.append("#e74c3c")  # red
        elif s < 0.6:
            colors.append("#f39c12")  # yellow/orange
        else:
            colors.append("#2ecc71")  # green
    df["Color"] = colors

    # Use plotly for horizontal bar chart with custom colors
    import plotly.graph_objects as go

    fig = go.Figure(go.Bar(
        x=df["Score"].tolist(),
        y=df["Concept"].tolist(),
        orientation="h",
        marker_color=df["Color"].tolist(),
        text=[f"{s:.2f}" for s in df["Score"]],
        textposition="outside",
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 1.05], title="Score"),
        yaxis=dict(title=""),
        height=max(200, len(rows) * 40 + 60),
        margin=dict(l=10, r=10, t=10, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_recall_timeline(recalls: list, title: str = "Recall Queue"):
    """Render a table of recall entries."""
    st.subheader(title)

    if not recalls:
        st.info("No recall entries.")
        return

    rows = []
    for r in recalls:
        if hasattr(r, "concept_key"):
            rows.append({
                "Concept": r.concept_key,
                "Source Video": getattr(r, "source_video_id", ""),
                "Due At": str(getattr(r, "due_at", "")),
                "Interval (hrs)": getattr(r, "interval_hours", ""),
                "Status": getattr(r, "status", "pending"),
            })
        elif isinstance(r, dict):
            rows.append({
                "Concept": r.get("concept_key", ""),
                "Source Video": r.get("source_video_id", ""),
                "Due At": str(r.get("due_at", "")),
                "Interval (hrs)": r.get("interval_hours", ""),
                "Status": r.get("status", "pending"),
            })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
