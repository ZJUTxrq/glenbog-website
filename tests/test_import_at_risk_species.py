from datetime import date

from scripts.import_at_risk_species import parse_at_risk_species_row


def make_row(**overrides):
    row = {
        "scientificName": "Testus birdus",
        "vernacularName": "Test Bird",
        "class": "Aves",
        "order": "Passeriformes",
        "number_of_observations": "3.0",
        "most_recent_observation": "2026-04-01",
        "at_risk_status": "Endangered",
        "decimalLatitude": "-35.123",
        "decimalLongitude": "149.456",
    }
    row.update(overrides)
    return row


def test_parse_at_risk_species_row_converts_csv_values():
    parsed = parse_at_risk_species_row(make_row())

    assert parsed == {
        "scientific_name": "Testus birdus",
        "common_name": "Test Bird",
        "class_display": "Aves",
        "order": "Passeriformes",
        "num_observations": 3,
        "date_of_observation": date(2026, 4, 1),
        "status": "Endangered",
        "latitude": -35.123,
        "longitude": 149.456,
    }


def test_parse_at_risk_species_row_handles_empty_optional_values():
    parsed = parse_at_risk_species_row(
        make_row(
            most_recent_observation="",
            decimalLatitude="",
            decimalLongitude="",
        )
    )

    assert parsed["date_of_observation"] is None
    assert parsed["latitude"] is None
    assert parsed["longitude"] is None
