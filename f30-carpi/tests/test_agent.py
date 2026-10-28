import json
from types import SimpleNamespace

import pytest

from carpi.agent import CarAgent, Toolbox
from carpi.agent.tools import TOOL_DEFINITIONS
from carpi.config import Settings
from carpi.events import EventBus
from carpi.media import SimulatedMedia
from carpi.phone import SimulatedPhone


def text(t):
    return SimpleNamespace(type="text", text=t)


def tool_use(id_, name, input_):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=input_)


def response(stop_reason, *content):
    return SimpleNamespace(stop_reason=stop_reason, content=list(content))


class FakeClient:
    """Ersetzt die Claude-API: liefert vorbereitete Antworten und merkt sich die Anfragen."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        # Kopie, da der Agent die Liste danach weiter ergänzt
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return self._responses.pop(0)


@pytest.fixture
def env():
    bus = EventBus()
    phone, media = SimulatedPhone(bus), SimulatedMedia(bus)
    return bus, phone, media


def make_agent(env, responses, **settings):
    bus, phone, media = env
    client = FakeClient(responses)
    agent = CarAgent(Settings(**settings), Toolbox(phone, media), bus, client=client)
    return agent, client


async def test_call_contact_via_tools(env):
    _, phone, _ = env
    agent, client = make_agent(
        env,
        [
            response("tool_use", tool_use("t1", "search_contacts", {"query": "mama"})),
            response("tool_use", tool_use("t2", "call", {"number": "+49 160 3333333"})),
            response("end_turn", text("Ich rufe Mama an.")),
        ],
    )
    reply = await agent.ask("Ruf Mama an")

    assert reply == "Ich rufe Mama an."
    assert phone.active_number == "+49 160 3333333"
    # Ergebnis der Kontaktsuche wurde an das Modell zurückgegeben
    result = client.requests[1]["messages"][-1]["content"][0]
    assert result["tool_use_id"] == "t1" and not result["is_error"]
    assert json.loads(result["content"])["contacts"][0]["name"] == "Mama"


async def test_request_uses_configured_model_and_fallbacks(env):
    agent, client = make_agent(env, [response("end_turn", text("Hallo!"))], model="claude-opus-5-5", effort="low")
    await agent.ask("Hallo")
    req = client.requests[0]
    assert req["model"] == "claude-opus-5-5"
    assert req["output_config"] == {"effort": "low"}
    assert req["thinking"] == {"type": "adaptive"}
    assert req["fallbacks"] == "default"
    assert req["betas"] == ["server-side-fallback-2026-07-01"]
    assert any(t.get("name") == "web_search" for t in req["tools"])


async def test_parallel_tool_results_in_one_message(env):
    _, _, media = env
    agent, client = make_agent(
        env,
        [
            response(
                "tool_use",
                tool_use("a", "set_volume", {"percent": 30}),
                tool_use("b", "play_music", {"query": "kraftwerk"}),
            ),
            response("end_turn", text("Läuft.")),
        ],
    )
    await agent.ask("Spiel Kraftwerk leiser")
    results = client.requests[1]["messages"][-1]["content"]
    assert [r["tool_use_id"] for r in results] == ["a", "b"]
    assert media.volume == 30


async def test_unknown_tool_is_reported_as_error(env):
    agent, client = make_agent(
        env,
        [response("tool_use", tool_use("x", "open_trunk", {})), response("end_turn", text("Geht nicht."))],
    )
    await agent.ask("Kofferraum auf")
    result = client.requests[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True


async def test_refusal_resets_conversation(env):
    agent, _ = make_agent(env, [response("refusal")])
    reply = await agent.ask("…")
    assert "nicht helfen" in reply
    assert agent.messages == []


async def test_pause_turn_is_resent(env):
    agent, client = make_agent(env, [response("pause_turn", text("Suche …")), response("end_turn", text("Sonnig."))])
    assert await agent.ask("Wetter in Berlin?") == "Sonnig."
    assert client.requests[1]["messages"][-1]["role"] == "assistant"


async def test_idle_conversation_starts_fresh(env):
    agent, client = make_agent(
        env, [response("end_turn", text("Eins")), response("end_turn", text("Zwei"))], agent_idle_reset_s=0
    )
    await agent.ask("erste Frage")
    agent._last_activity -= 10
    await agent.ask("zweite Frage")
    assert client.requests[1]["messages"] == [{"role": "user", "content": "zweite Frage"}]


def test_tool_schemas_are_strict():
    for tool in TOOL_DEFINITIONS:
        schema = tool["input_schema"]
        assert tool["strict"] is True
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
