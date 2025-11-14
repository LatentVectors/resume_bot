from __future__ import annotations

import streamlit as st


def _normalize_status_label(status: object) -> str:
    """Return a user-facing status label from a string or Enum-like value.

    Accepts raw strings or enum-like objects with a ``value`` attribute and
    normalizes them to one of the allowed labels.
    """
    allowed: tuple[str, ...] = (
        "Saved",
        "Applied",
        "Interviewing",
        "Not Selected",
        "No Offer",
        "Hired",
    )

    raw: str
    if isinstance(status, str):
        raw = status
    else:
        val = getattr(status, "value", None)
        raw = val if isinstance(val, str) else str(status)

    raw = (raw or "").strip()
    if raw in allowed:
        return raw

    if "." in raw:
        raw = raw.split(".")[-1]

    name_to_label: dict[str, str] = {
        "Saved": "Saved",
        "Applied": "Applied",
        "Interviewing": "Interviewing",
        "NotSelected": "Not Selected",
        "NoOffer": "No Offer",
        "Hired": "Hired",
    }
    return name_to_label.get(raw, "Saved")


def render_status_badge(status: object) -> None:
    """Render a consistent status badge with an icon and color.

    Args:
        status: Value compatible with the allowed status labels.
    """
    label = _normalize_status_label(status)
    icon_prefix_map: dict[str, str] = {
        "Saved": ":material/bookmark:",
        "Applied": ":material/send:",
        "Interviewing": ":material/question_answer:",
        "Not Selected": ":material/cancel:",
        "No Offer": ":material/thumb_down:",
        "Hired": ":material/task_alt:",
    }
    color_map: dict[str, str] = {
        "Saved": "gray",
        "Applied": "green",
        "Interviewing": "green",
        "Not Selected": "red",
        "No Offer": "red",
        "Hired": "green",
    }

    st.badge(label=label, icon=icon_prefix_map[label], color=color_map[label])
