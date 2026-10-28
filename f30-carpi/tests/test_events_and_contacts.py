import pytest

from carpi.events import EventBus
from carpi.phone.base import Contact, find_contacts


async def test_bus_delivers_to_all_subscribers():
    bus = EventBus()
    async with bus.subscribe() as a, bus.subscribe() as b:
        bus.publish({"type": "x"})
        assert a.get_nowait() == {"type": "x"}
        assert b.get_nowait() == {"type": "x"}
    bus.publish({"type": "y"})  # nach dem Abmelden kein Fehler


async def test_bus_drops_oldest_when_full():
    bus = EventBus(queue_size=2)
    async with bus.subscribe() as q:
        for i in range(3):
            bus.publish({"type": "n", "i": i})
        assert [q.get_nowait()["i"], q.get_nowait()["i"]] == [1, 2]


def test_event_needs_type():
    with pytest.raises(ValueError):
        EventBus().publish({"text": "ohne Typ"})


def test_find_contacts_ranks_exact_then_prefix_then_partial():
    contacts = [Contact("Annabell", "1"), Contact("Hanna", "2"), Contact("Anna", "3"), Contact("Bob", "4")]
    assert [c.name for c in find_contacts(contacts, "anna")] == ["Anna", "Annabell", "Hanna"]
    assert find_contacts(contacts, "  ") == []
