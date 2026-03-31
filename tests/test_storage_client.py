import pytest
from storage.base import get_storage_client


@pytest.fixture(scope="module")
def client():
    return get_storage_client()


def test_put_and_get_json(client):
    client.put_json("test/round_trip.json", {"ok": True, "value": 42})
    result = client.get_json("test/round_trip.json")
    assert result == {"ok": True, "value": 42}


def test_put_and_get_text(client):
    client.put_text("test/hello.txt", "hello world")
    result = client.get_text("test/hello.txt")
    assert result == "hello world"


def test_exists_true(client):
    client.put_json("test/exists_check.json", {"x": 1})
    assert client.exists("test/exists_check.json") is True


def test_exists_false(client):
    assert client.exists("test/does_not_exist.json") is False


def test_list_keys(client):
    client.put_json("test/list_a.json", {})
    client.put_json("test/list_b.json", {})
    keys = client.list_keys("test/list_")
    assert "test/list_a.json" in keys
    assert "test/list_b.json" in keys
