from carpi.vehicle.idrive import ButtonSpec, IDriveDecoder, IDriveMap, RotarySpec, SignalSpec


def make_decoder(width: int = 1, invert: bool = False) -> IDriveDecoder:
    mapping = IDriveMap(
        rotary=RotarySpec(can_id=0x100, byte=2, width=width, invert=invert),
        buttons=[ButtonSpec(name="enter", can_id=0x101, byte=0, mask=0x0F, value=0x01)],
    )
    return IDriveDecoder(mapping)


def rotary_frame(counter: int, width: int = 1) -> bytes:
    return bytes([0, 0]) + counter.to_bytes(width, "little") + bytes(4)


def test_first_rotary_frame_only_sets_baseline():
    dec = make_decoder()
    assert dec.feed(0x100, rotary_frame(10)) == []


def test_rotary_forward_and_backward():
    dec = make_decoder()
    dec.feed(0x100, rotary_frame(10))
    assert dec.feed(0x100, rotary_frame(12)) == [{"type": "nav", "action": "rotate", "delta": 2}]
    assert dec.feed(0x100, rotary_frame(11)) == [{"type": "nav", "action": "rotate", "delta": -1}]


def test_rotary_wraps_around():
    dec = make_decoder()
    dec.feed(0x100, rotary_frame(0xFF))
    assert dec.feed(0x100, rotary_frame(0x01))[0]["delta"] == 2
    assert dec.feed(0x100, rotary_frame(0xFE))[0]["delta"] == -3


def test_rotary_16bit_and_invert():
    dec = make_decoder(width=2, invert=True)
    dec.feed(0x100, rotary_frame(0xFFFF, width=2))
    assert dec.feed(0x100, rotary_frame(0x0000, width=2))[0]["delta"] == -1


def test_button_reports_only_on_press_edge():
    dec = make_decoder()
    pressed, released = bytes([0xF1]), bytes([0xF0])  # obere Bits werden ausmaskiert
    assert dec.feed(0x101, pressed) == [{"type": "nav", "action": "press", "button": "enter"}]
    assert dec.feed(0x101, pressed) == []  # gedrückt halten: keine Wiederholung
    assert dec.feed(0x101, released) == []
    assert dec.feed(0x101, pressed)[0]["button"] == "enter"


def test_ignition_from_can_reports_changes_only():
    mapping = IDriveMap(ignition=SignalSpec(can_id=0x12, byte=0, mask=0x0F, value=0x0A))
    dec = IDriveDecoder(mapping)
    on, off = bytes([0x4A]), bytes([0x48])
    assert dec.feed(0x12, on) == [{"type": "vehicle.ignition", "on": True, "source": "can"}]
    assert dec.feed(0x12, on) == []
    assert dec.feed(0x12, off) == [{"type": "vehicle.ignition", "on": False, "source": "can"}]
    assert mapping.can_ids == {0x12}


def test_short_or_foreign_frames_are_ignored():
    dec = make_decoder()
    assert dec.feed(0x100, b"\x00") == []
    assert dec.feed(0x555, rotary_frame(3)) == []


def test_load_map_from_toml(tmp_path):
    path = tmp_path / "map.toml"
    path.write_text(
        """
[rotary]
can_id = 0x264
byte = 3
width = 2

[[buttons]]
name = "back"
can_id = 0x267
byte = 5
mask = 0x20
value = 0x20

[ignition]
can_id = 0x12F
byte = 0
mask = 0x0F
value = 0x0A
""",
        encoding="utf-8",
    )
    mapping = IDriveMap.load(path)
    assert mapping.rotary == RotarySpec(can_id=0x264, byte=3, width=2)
    assert mapping.buttons[0].name == "back"
    assert mapping.ignition == SignalSpec(can_id=0x12F, byte=0, mask=0x0F, value=0x0A)
    assert mapping.can_ids == {0x264, 0x267, 0x12F}


def test_shipped_template_map_is_empty():
    from carpi.config import PROJECT_ROOT

    mapping = IDriveMap.load(PROJECT_ROOT / "config" / "idrive_map.toml")
    assert mapping.rotary is None and mapping.buttons == [] and mapping.ignition is None
