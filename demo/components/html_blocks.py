"""HTML rendering helpers for the demo UI.

Card backgrounds use CSS custom properties (--card-*) defined in app.py,
so they adapt to light/dark mode automatically.
"""

import json
import streamlit as st
import streamlit.components.v1 as components


# ---------------------------------------------------------------------------
# Colour tokens (text/border accents only — backgrounds come from CSS vars)
# ---------------------------------------------------------------------------
BLUE = "#4A90D9"
ORANGE = "#E67E22"
GREEN = "#2ecc71"
RED = "#e74c3c"
YELLOW = "#f39c12"

_LEARNER_TAG = (
    '<span style="font-size:0.52rem;font-weight:700;letter-spacing:0.08em;'
    'text-transform:uppercase;padding:2px 7px;border-radius:4px;'
    f'background:rgba(74,144,217,0.1);color:{BLUE};'
    'margin-bottom:8px;display:inline-block;">Learner sees this</span>'
)


def _md(html: str):
    """Render HTML via st.markdown (flows naturally, no fixed height)."""
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Panel headers
# ---------------------------------------------------------------------------

def panel_header_learner():
    _md(f'<div style="font-size:0.7rem;font-weight:700;letter-spacing:0.12em;'
        f'text-transform:uppercase;padding:6px 0 10px 0;'
        f'border-bottom:2px solid rgba(128,128,128,0.12);'
        f'color:{BLUE};margin-bottom:12px;">What Happens</div>')


def panel_header_system():
    _md(f'<div style="font-size:0.7rem;font-weight:700;letter-spacing:0.12em;'
        f'text-transform:uppercase;padding:6px 0 10px 0;'
        f'border-bottom:2px solid rgba(128,128,128,0.12);'
        f'color:{ORANGE};margin-bottom:12px;">Under the Hood</div>')


# ---------------------------------------------------------------------------
# Step indicator (only element using components.html)
# ---------------------------------------------------------------------------

def step_indicator(labels: list[str], current: int):
    """Horizontal step progress bar. current is 1-indexed."""
    if current < 1:
        return

    nodes = []
    for i, label in enumerate(labels):
        step_num = i + 1
        if step_num < current:
            dot_bg, dot_color, icon = GREEN, "#fff", "&#10003;"
            label_color, label_weight = GREEN, "400"
        elif step_num == current:
            dot_bg, dot_color, icon = BLUE, "#fff", str(step_num)
            label_color, label_weight = BLUE, "700"
        else:
            dot_bg = "rgba(128,128,128,0.22)"
            dot_color = "rgba(128,128,128,0.55)"
            icon = str(step_num)
            label_color, label_weight = "rgba(128,128,128,0.4)", "400"

        connector = ""
        if i < len(labels) - 1:
            c = GREEN if step_num < current else "rgba(128,128,128,0.15)"
            connector = f'<div style="position:absolute;top:11px;left:50%;width:100%;height:2px;background:{c};z-index:0;"></div>'

        shadow = "box-shadow:0 0 0 3px rgba(74,144,217,0.2);" if step_num == current else ""
        nodes.append(
            f'<div style="display:flex;flex-direction:column;align-items:center;flex:1;position:relative;">'
            f'{connector}'
            f'<div style="width:22px;height:22px;border-radius:50%;display:flex;align-items:center;'
            f'justify-content:center;font-size:0.6rem;font-weight:700;color:{dot_color};'
            f'background:{dot_bg};z-index:1;{shadow}">{icon}</div>'
            f'<div style="font-size:0.58rem;margin-top:3px;text-align:center;white-space:nowrap;'
            f'color:{label_color};font-weight:{label_weight};">{label}</div>'
            f'</div>'
        )

    base_css = ('<style>*{box-sizing:border-box;margin:0;padding:0;}'
                'body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;'
                'background:transparent;color:rgba(250,250,250,0.87);}'
                '@media(prefers-color-scheme:light){body{color:rgba(0,0,0,0.87);}}</style>')
    inner = f'<div style="display:flex;align-items:center;gap:0;padding:4px 0;">{"".join(nodes)}</div>'
    components.html(f"{base_css}{inner}", height=52, scrolling=False)


# ===========================================================================
# LEFT PANEL — "Learner visible" cards (blue, with tag)
# ===========================================================================

def learner_visible_card(title: str, body: str, icon: str = ""):
    """Card for content the learner would see in production."""
    title_part = (f'<div style="font-size:0.92rem;font-weight:700;color:{BLUE};margin-bottom:6px;">'
                  f'{icon}{" " if icon else ""}{title}</div>') if title else ""
    _md(f'<div style="border:1.5px solid var(--card-learner-border);border-radius:12px;'
        f'padding:16px 20px;margin-bottom:12px;background:var(--card-learner-bg);">'
        f'{_LEARNER_TAG}'
        f'{title_part}'
        f'<div style="font-size:0.85rem;line-height:1.6;">{body}</div>'
        f'</div>')


def recap_card(concept: str, bullet: str, tone: str):
    """Learner-visible: recap bullet."""
    tone_icon = "&#127919;" if tone == "AS" else "&#128161;"
    _md(f'<div style="border:1.5px solid var(--card-learner-border);border-radius:12px;'
        f'padding:14px 18px;margin-bottom:10px;background:var(--card-learner-bg);">'
        f'{_LEARNER_TAG}'
        f'<div style="font-size:0.88rem;font-weight:700;color:{BLUE};margin-bottom:5px;">'
        f'{tone_icon} {concept}</div>'
        f'<div style="font-size:0.83rem;line-height:1.6;">{bullet}</div>'
        f'</div>')


def quiz_result_card(index: int, concept: str, correct: bool, answer_text: str = ""):
    """Learner-visible: quiz result."""
    if correct:
        border, bg, color = "rgba(46,204,113,0.35)", "rgba(46,204,113,0.08)", GREEN
        icon_char, msg = "&#10003;", "Correct"
    else:
        border, bg, color = "rgba(231,76,60,0.35)", "rgba(231,76,60,0.08)", RED
        icon_char = "&#10007;"
        msg = f"The answer was: {answer_text}" if answer_text else "Incorrect"

    _md(f'<div style="border:1.5px solid {border};border-radius:12px;'
        f'padding:14px 18px;margin-bottom:10px;background:{bg};">'
        f'{_LEARNER_TAG}'
        f'<div style="font-size:0.88rem;font-weight:700;color:{color};margin-bottom:4px;">'
        f'{icon_char} Q{index}: {concept}</div>'
        f'<div style="font-size:0.83rem;">{msg}</div>'
        f'</div>')


def recommendation_card(tag: str, tag_type: str, title: str, subtitle: str):
    """Learner-visible: recommendation slot."""
    tag_bg = "rgba(46,204,113,0.12)" if tag_type == "series" else "rgba(74,144,217,0.12)"
    tag_color = GREEN if tag_type == "series" else BLUE

    _md(f'<div style="border:1.5px solid var(--card-learner-border);border-radius:12px;'
        f'padding:14px 18px;margin-bottom:10px;background:var(--card-learner-bg);">'
        f'{_LEARNER_TAG}'
        f'<span style="font-size:0.58rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;'
        f'padding:2px 8px;border-radius:4px;display:inline-block;margin-bottom:6px;'
        f'background:{tag_bg};color:{tag_color};">{tag}</span>'
        f'<div style="font-weight:700;font-size:0.9rem;margin-bottom:3px;">{title}</div>'
        f'<div style="font-size:0.74rem;opacity:0.6;">{subtitle}</div>'
        f'</div>')


def progress_card(message: str):
    """Learner-visible: progress update."""
    _md(f'<div style="border:1.5px solid rgba(46,204,113,0.3);border-radius:12px;'
        f'padding:16px 20px;margin-bottom:12px;background:rgba(46,204,113,0.08);">'
        f'{_LEARNER_TAG}'
        f'<div style="font-size:0.88rem;font-weight:700;color:{GREEN};margin-bottom:5px;">Progress Update</div>'
        f'<div style="font-size:0.85rem;line-height:1.6;">{message}</div>'
        f'</div>')


# ===========================================================================
# LEFT PANEL — "Event" cards (neutral, no tag — demo narrative only)
# ===========================================================================

def event_card(title: str, body: str):
    """Neutral card for demo narrative steps the learner would NOT see."""
    title_part = (f'<div style="font-size:0.88rem;font-weight:600;margin-bottom:5px;">'
                  f'{title}</div>') if title else ""
    _md(f'<div style="border:1px solid var(--card-event-border);border-radius:10px;'
        f'padding:14px 18px;margin-bottom:12px;background:var(--card-event-bg);">'
        f'{title_part}'
        f'<div style="font-size:0.83rem;line-height:1.5;opacity:0.85;">{body}</div>'
        f'</div>')


def user_profile_card(name: str, type_display: str, maturity: str, videos: int):
    """Event card: user profile (evaluator context, not shown to learner)."""
    _md(f'<div style="border:1px solid var(--card-event-border);border-radius:10px;'
        f'padding:14px 18px;margin-bottom:12px;background:var(--card-event-bg);">'
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
        f'<div style="width:34px;height:34px;border-radius:50%;background:rgba(128,128,128,0.2);'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-weight:700;font-size:0.9rem;">{name[0]}</div>'
        f'<div><div style="font-weight:700;font-size:0.95rem;">{name}</div>'
        f'<div style="font-size:0.72rem;opacity:0.55;">{type_display}</div></div></div>'
        f'<div style="display:flex;gap:6px;flex-wrap:wrap;">'
        f'<span style="display:inline-flex;align-items:center;padding:4px 10px;border-radius:12px;'
        f'font-size:0.7rem;font-weight:500;border:1px solid rgba(128,128,128,0.15);'
        f'background:rgba(128,128,128,0.06);">{maturity}</span>'
        f'<span style="display:inline-flex;align-items:center;padding:4px 10px;border-radius:12px;'
        f'font-size:0.7rem;font-weight:500;border:1px solid rgba(128,128,128,0.15);'
        f'background:rgba(128,128,128,0.06);">{videos} videos watched</span>'
        f'</div></div>')


def journey_prestart_card(title: str, description: str, context: str):
    """Styled card for the journey landing/prestart screen."""
    _md(
        f'<div style="border:1px solid var(--card-prestart-border);border-radius:12px;'
        f'padding:20px 24px;margin-bottom:14px;'
        f'background:var(--card-prestart-bg);">'
        f'<div style="font-size:1.1rem;font-weight:700;margin-bottom:8px;">{title}</div>'
        f'<div style="font-size:0.85rem;line-height:1.6;opacity:0.85;margin-bottom:10px;">'
        f'{description}</div>'
        f'<div style="font-size:0.72rem;opacity:0.5;">{context}</div>'
        f'</div>'
    )


def journey_complete_banner(journey_name: str):
    _md(f'<div style="border:2px solid {GREEN};border-radius:12px;padding:16px 24px;'
        f'text-align:center;margin:16px 0;background:rgba(46,204,113,0.06);">'
        f'<div style="color:{GREEN};font-weight:700;font-size:1.05rem;margin-bottom:3px;">Journey Complete</div>'
        f'<div style="font-size:0.8rem;opacity:0.7;">{journey_name}</div>'
        f'</div>')


# ===========================================================================
# Step navigation (Back / Next)
# ===========================================================================

_PANEL_HEIGHT = 520


def scroll_to_top():
    """Inject JS to scroll Streamlit's main container to the top."""
    if st.session_state.pop("_scroll_top", False):
        components.html(
            '<script>window.parent.document.querySelector("section.main").scrollTo(0,0);</script>',
            height=0,
        )


def step_columns(step_key: str = ""):
    """Return (left, right) fixed-height scrollable containers inside two columns."""
    col_l, col_r = st.columns(2)
    with col_l:
        left = st.container(height=_PANEL_HEIGHT, border=False,
                            key=f"_lp_{step_key}" if step_key else None)
    with col_r:
        right = st.container(height=_PANEL_HEIGHT, border=False,
                             key=f"_rp_{step_key}" if step_key else None)
    return left, right


def step_nav(prefix: str, current_step: int, total_steps: int,
             set_step_fn, show_next: bool = True,
             invalidate_from: dict | None = None):
    """Render Back / Next buttons for journey navigation.

    current_step is 1-indexed. Back is hidden on step 1.
    Next is hidden on the final step or when show_next=False (e.g. quiz).

    invalidate_from: optional dict mapping step number -> list of session
    state keys to clear.  When going back, all keys for the current step
    and every later step are removed so downstream results are recomputed
    with updated inputs (e.g. changed quiz answers).
    """
    show_back = current_step > 1
    show_fwd = show_next and current_step < total_steps

    if not show_back and not show_fwd:
        return

    back_col, _, fwd_col = st.columns([1, 6, 1])
    if show_back:
        with back_col:
            if st.button("← Back", key=f"{prefix}_back_{current_step}", type="primary"):
                if invalidate_from:
                    for step_num, keys in invalidate_from.items():
                        if step_num >= current_step:
                            for k in keys:
                                st.session_state.pop(k, None)
                set_step_fn(current_step - 1)
                st.session_state["_scroll_top"] = True
                st.rerun()
    if show_fwd:
        with fwd_col:
            if st.button("Next →", key=f"{prefix}_to_step{current_step + 1}", type="primary"):
                set_step_fn(current_step + 1)
                st.session_state["_scroll_top"] = True
                st.rerun()


# ===========================================================================
# RIGHT PANEL — System code blocks (orange)
# ===========================================================================

def system_code_block(label: str, content: str):
    _md(
        f'<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;'
        f'color:{ORANGE};margin-bottom:2px;margin-top:10px;">{label}</div>'
    )
    st.code(content, language=None)


def _spaced_json(data) -> str:
    """JSON with blank lines between top-level keys and array items."""
    try:
        raw = json.dumps(data, indent=2, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(data)

    if not isinstance(data, (dict, list)) or len(data) <= 1:
        return raw

    lines = raw.splitlines()
    spaced = []
    depth = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("}") or stripped.startswith("]"):
            depth -= 1
        need_gap = False
        if depth == 1 and stripped.startswith('"') and spaced:
            need_gap = True
        if depth >= 2 and stripped == "{" and spaced and not spaced[-1].rstrip().endswith("["):
            need_gap = True
        if need_gap and spaced and spaced[-1] != "":
            spaced.append("")
        spaced.append(line)
        if stripped.endswith("{") or stripped.endswith("["):
            depth += 1
    return "\n".join(spaced)


def system_json_block(label: str, data):
    system_code_block(label, _spaced_json(data))


def system_note(text: str):
    """Small styled note for contextual hints on the system panel."""
    _md(
        f'<div style="font-size:0.68rem;line-height:1.5;padding:6px 12px;margin-bottom:10px;'
        f'border-left:2px solid {ORANGE};opacity:0.7;font-style:italic;">'
        f'{text}</div>'
    )
