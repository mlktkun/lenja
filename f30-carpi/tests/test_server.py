from fastapi.testclient import TestClient

from carpi.config import Settings
from carpi.server import build_services, create_app


class NoAgentClient:
    beta = None


def make_client():
    services = build_services(Settings(mode="sim"), agent_client=NoAgentClient())
    return TestClient(create_app(services)), services


def test_status_and_ui_are_served():
    client, _ = make_client()
    with client:
        status = client.get("/api/status").json()
        assert status["mode"] == "sim"
        assert status["media"]["title"]
        assert "F30 CarPi" in client.get("/").text


def test_websocket_media_and_phone_commands():
    client, services = make_client()
    with client, client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "media.control", "action": "next"})
        event = ws.receive_json()
        assert event["type"] == "media.state" and event["title"] == "Major Tom"

        ws.send_json({"cmd": "phone.contacts"})
        contacts = ws.receive_json()
        assert contacts["type"] == "phone.contacts" and len(contacts["contacts"]) == 3

        ws.send_json({"cmd": "phone.dial", "number": "123"})
        assert ws.receive_json() == {"type": "phone.call", "state": "dialing", "number": "123"}
        assert services.phone.active_number == "123"


def test_bad_command_reports_error():
    client, _ = make_client()
    with client, client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "media.control", "action": "explode"})
        event = ws.receive_json()
        assert event["type"] == "error"
