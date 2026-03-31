import pytest
from llm.base import get_llm_client


@pytest.fixture(scope="module")
def client():
    return get_llm_client()


def test_generate_returns_string(client):
    result = client.generate("Say hello in one sentence.")
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_json_returns_dict(client):
    result = client.generate_json(
        "Return a JSON object with keys name (string) and score (number).",
        schema={"name": "string", "score": "number"},
    )
    assert isinstance(result, dict)
    assert "name" in result
    assert "score" in result


def test_generate_json_with_system_prompt(client):
    result = client.generate_json(
        "Return the result.",
        system="You are a test assistant.",
        schema={"status": "string"},
    )
    assert isinstance(result, dict)
