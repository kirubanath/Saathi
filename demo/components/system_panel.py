"""System reasoning panel components.

These render the right panel — what the evaluator sees.
Raw data dumps (JSON) with clear headings and separators,
so it looks like a peek "under the hood" — not a polished UI.
"""

import streamlit as st

from demo.components.html_blocks import (
    panel_header_system,
    system_code_block,
    system_json_block,
)


def render_panel_header():
    panel_header_system()


def render_classification(classification: dict):
    """Dump classification result + reasoning in one block."""
    output = {
        "content_type": classification.get("content_type", ""),
        "user_type": classification.get("user_type", ""),
        "maturity": classification.get("maturity", ""),
        "flags": {
            "show_recap": classification.get("show_recap", False),
            "show_quiz": classification.get("show_quiz", False),
            "show_recall": classification.get("show_recall", False),
            "max_bullets": classification.get("max_bullets", 0),
            "difficulty_cap": classification.get("difficulty_cap"),
        },
        "reasoning": classification.get("reasoning", []),
    }
    system_json_block("Classification", output)


def render_concept_ranking(bullets: list[dict], concept_profile: dict | None = None):
    """Dump concept ranking as JSON."""
    if not bullets:
        return

    rows = []
    for b in sorted(bullets, key=lambda x: x.get("rank", 0)):
        rows.append({
            "rank": b.get("rank", 0),
            "concept": b["concept"],
            "coverage": round(b.get("coverage_score", 0), 3),
            "gap": round(b.get("gap_score", 0), 3),
            "score": round(b.get("coverage_score", 0) * b.get("gap_score", 0), 3),
            "tone": b.get("tone", ""),
        })

    system_json_block("Concept Ranking (coverage × gap)", rows)

    if concept_profile:
        system_json_block("Video Concept Profile", concept_profile)


def render_knowledge_comparison(delta: dict):
    """Dump before/after knowledge delta as JSON."""
    if not delta:
        system_json_block("Knowledge Delta", {"status": "no changes"})
        return

    output = {}
    for concept, d in delta.items():
        before = d.get("before", 0)
        after = d.get("after", 0)
        output[concept] = {
            "before": round(before, 3),
            "after": round(after, 3),
            "change": round(after - before, 3),
        }

    system_json_block("Knowledge Delta", output)


def render_watch_bump(watch_update_delta: dict):
    """Dump watch bump delta as JSON with formula note."""
    if not watch_update_delta:
        return
    render_knowledge_comparison(watch_update_delta)
    st.caption("`formula: new = min(0.8, old + 0.1 × completion_rate × coverage)`")


def _parse_candidate_line(line: str) -> dict | None:
    """Parse a reasoning candidate line like 'vid_004: relevance=1.39, probability=65.2%'."""
    parts = line.split(":", 1)
    if len(parts) < 2:
        return None
    vid = parts[0].strip()
    attrs: dict[str, str] = {}
    note = None
    remainder = parts[1]
    if "[" in remainder:
        remainder, bracket = remainder.split("[", 1)
        note = bracket.rstrip("]").strip()
    for seg in remainder.split(","):
        seg = seg.strip()
        if "=" in seg:
            k, v = seg.split("=", 1)
            attrs[k.strip()] = v.strip()
    entry = {"video": vid}
    entry.update(attrs)
    if note:
        entry["note"] = note
    return entry


def render_recommendation_breakdown(recommendation: dict):
    """Parse recommendation reasoning into structured JSON blocks."""
    if not recommendation:
        return

    reasoning = recommendation.get("reasoning", [])
    if not reasoning:
        return

    slot1_lines = []
    pool_info = None
    config = None
    candidates = []
    bucket_lines = []
    bucket_selected = None
    selected = None

    for line in reasoning:
        s = line.strip()
        if s.startswith("Slot 1:"):
            slot1_lines.append(s)
        elif "pool:" in s.lower():
            pool_info = s
        elif s.startswith("Aspiration") or s.startswith("Softmax"):
            config = s
        elif s.startswith("\u2192 bucket selected:") or s.startswith("bucket selected:"):
            bucket_selected = s.split(":", 1)[1].strip().strip("'")
        elif "probability=" in s:
            candidates.append(s)
        elif s.startswith("Slot 2 selected:"):
            selected = s
        elif s.startswith("bucket ") or s.startswith("Bucket split"):
            bucket_lines.append(s)
        elif not s.startswith("Slot 1"):
            slot1_lines.append(s)

    if slot1_lines:
        system_json_block("Slot 1 — Series Continuation", slot1_lines)

    if bucket_lines and candidates:
        pool_data = {}
        if pool_info:
            pool_data["pool"] = pool_info
        if config:
            pool_data["sampling"] = config

        bucket_alloc = {}
        for bl in bucket_lines:
            bl = bl.strip()
            if bl.startswith("bucket '"):
                bparts = bl.split("'", 2)
                if len(bparts) >= 3:
                    bucket_alloc[bparts[1]] = bparts[2].lstrip(":").strip()
        if bucket_alloc:
            pool_data["buckets"] = bucket_alloc
        if bucket_selected:
            pool_data["bucket_selected"] = bucket_selected

        parsed = [e for line in candidates if (e := _parse_candidate_line(line))]
        pool_data["candidates"] = parsed
        if selected:
            pool_data["selected"] = selected
        system_json_block("Slot 2 — Engine Pick", pool_data)

    elif candidates:
        pool_data = {}
        if pool_info:
            pool_data["pool"] = pool_info
        if config:
            pool_data["sampling"] = config
        parsed = [e for line in candidates if (e := _parse_candidate_line(line))]
        pool_data["candidates"] = parsed
        if selected:
            pool_data["selected"] = selected
        system_json_block("Slot 2 — Engine Pick", pool_data)

    elif bucket_lines:
        bucket_data = {}
        if pool_info:
            bucket_data["pool"] = pool_info
        bucket_data["buckets"] = bucket_lines
        if selected:
            bucket_data["selected"] = selected
        system_json_block("Slot 2 — Bucket Pick", bucket_data)


def render_recall_details(recalls_scheduled: int, recall_details: list[dict] | None = None, reasoning: list[str] | None = None):
    """Dump recall scheduling info as JSON."""
    data = {
        "recalls_scheduled": recalls_scheduled,
        "interval_rules": {
            "score < 0.4": "18h",
            "0.4 <= score <= 0.6": "30h",
            "score > 0.6": "48h",
        },
    }

    if recall_details:
        entries = []
        for r in recall_details:
            entries.append({
                "concept_key": r.get("concept_key", ""),
                "source_video": r.get("source_video_id", ""),
                "due_at": r.get("due_at", ""),
                "interval": f"{r.get('interval_hours', 0):.0f}h",
            })
        data["entries"] = entries

    if reasoning:
        data["details"] = reasoning

    system_json_block("Recall Scheduling", data)


def render_reasoning_log(reasoning: list[str], title: str = "Reasoning Log"):
    """Dump reasoning steps as JSON list."""
    if not reasoning:
        return
    system_json_block(title, reasoning)


def render_quiz_difficulty(questions: list[dict], knowledge_before: dict | None = None):
    """Dump quiz difficulty selection as JSON."""
    if not questions:
        return

    rule = "< 0.4 → easy | 0.4–0.7 → medium | > 0.7 → hard"
    entries = []
    for q in questions:
        score = None
        if knowledge_before:
            for cat_concepts in knowledge_before.values():
                if q["concept"] in cat_concepts:
                    score = round(cat_concepts[q["concept"]], 3)
                    break

        entries.append({
            "concept": q["concept"],
            "current_score": score if score is not None else "N/A",
            "difficulty_assigned": q["difficulty"],
        })

    system_json_block("Quiz Difficulty Selection", {
        "rule": rule,
        "questions": entries,
    })


def render_skipped_steps(steps: list[tuple[str, str]]):
    """Dump skipped pipeline steps as JSON."""
    output = []
    for step_name, reason in steps:
        output.append({"step": step_name, "reason": reason, "status": "SKIP"})
    system_json_block("Skipped Pipeline Steps", output)


def render_comparison_table(priya_data: dict, rahul_data: dict):
    """Side-by-side comparison as JSON."""
    system_json_block("Priya vs Rahul", {
        "priya": priya_data,
        "rahul": rahul_data,
    })
