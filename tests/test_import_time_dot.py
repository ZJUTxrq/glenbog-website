from datetime import date

from scripts.import_time_dot import parse_time_dot_row


def test_parse_time_dot_row_converts_values():
    parsed = parse_time_dot_row({
        "scientificName": "Testus birdus",
        "vernacularName": "Test Bird",
        "class": "Aves",
        "order": "Passeriformes",
        "family": "Testidae",
        "eventDate": "2026-04-01",
    })

    assert parsed["event_date"] == date(2026, 4, 1)
    assert parsed["family"] == "Testidae"


def test_parse_time_dot_row_skips_missing_event_date():
    assert parse_time_dot_row({
        "scientificName": "Testus birdus",
        "vernacularName": "Test Bird",
        "eventDate": "",
    }) is None
