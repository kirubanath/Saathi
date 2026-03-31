"""Thin HTTP client for the Saathi FastAPI backend.

All demo pages import from here instead of calling engine/db directly.
"""

import os

import httpx

API_BASE = os.getenv("SAATHI_API_URL", "http://localhost:8000")
_TIMEOUT = 30.0


def _url(path: str) -> str:
    return f"{API_BASE}{path}"


def _raise_on_error(resp: httpx.Response) -> None:
    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        raise RuntimeError(f"API error {resp.status_code}: {detail}")


def list_users() -> list[dict]:
    resp = httpx.get(_url("/users"), timeout=_TIMEOUT)
    _raise_on_error(resp)
    return resp.json()["users"]


def list_videos() -> list[dict]:
    resp = httpx.get(_url("/videos"), timeout=_TIMEOUT)
    _raise_on_error(resp)
    return resp.json()["videos"]


def get_user(user_id: str) -> dict:
    resp = httpx.get(_url(f"/user/{user_id}"), timeout=_TIMEOUT)
    _raise_on_error(resp)
    return resp.json()["user"]


def video_complete(user_id: str, video_id: str, completion_rate: float = 1.0) -> dict:
    resp = httpx.post(
        _url("/video/complete"),
        json={"user_id": user_id, "video_id": video_id, "completion_rate": completion_rate},
        timeout=_TIMEOUT,
    )
    _raise_on_error(resp)
    return resp.json()


def quiz_submit(user_id: str, video_id: str, questions: list[dict], answers: list[dict]) -> dict:
    resp = httpx.post(
        _url("/quiz/submit"),
        json={
            "user_id": user_id,
            "video_id": video_id,
            "questions": questions,
            "answers": answers,
        },
        timeout=_TIMEOUT,
    )
    _raise_on_error(resp)
    return resp.json()


def session_start(user_id: str, simulated_time: str | None = None) -> dict:
    body: dict = {"user_id": user_id}
    if simulated_time:
        body["simulated_time"] = simulated_time
    resp = httpx.post(_url("/session/start"), json=body, timeout=_TIMEOUT)
    _raise_on_error(resp)
    return resp.json()


def recall_answer(user_id: str, recall_id: int, answer_index: int) -> dict:
    resp = httpx.post(
        _url("/recall/answer"),
        json={"user_id": user_id, "recall_id": recall_id, "answer_index": answer_index},
        timeout=_TIMEOUT,
    )
    _raise_on_error(resp)
    return resp.json()


def health_check() -> bool:
    try:
        resp = httpx.get(_url("/health"), timeout=3.0)
        return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
