from datetime import date

from scripts.import_survey_map import parse_survey_map_row


def test_parse_survey_map_row_converts_values():
    parsed = parse_survey_map_row({
        "scientificName": "Testus birdus",
        "vernacularName": "Test Bird",
        "eventDate": "2026-04-01",
        "dataResourceName": "Survey",
        "recordedBy": "Observer",
        "decimalLatitude": "-35.1",
        "decimalLongitude": "149.2",
    })

    assert parsed["event_date"] == date(2026, 4, 1)
    assert parsed["latitude"] == -35.1
    assert parsed["longitude"] == 149.2


def test_parse_survey_map_row_skips_missing_coordinates():
    assert parse_survey_map_row({
        "scientificName": "Testus birdus",
        "vernacularName": "Test Bird",
        "eventDate": "2026-04-01",
        "dataResourceName": "Survey",
        "recordedBy": "Observer",
        "decimalLatitude": "",
        "decimalLongitude": "149.2",
    }) is None
