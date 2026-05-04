from datetime import date

from scripts.import_species import parse_species_row


def test_parse_species_row_converts_values():
    parsed = parse_species_row({
        "class_display": "Aves",
        "order": "Passeriformes",
        "scientificName_clean": "Testus birdus",
        "vernacularName": "Test Bird",
        "num_observations": "7",
        "most_recent_date": "2026-04-01",
    })

    assert parsed["scientific_name"] == "Testus birdus"
    assert parsed["num_observations"] == 7
    assert parsed["most_recent_date"] == date(2026, 4, 1)


def test_parse_species_row_handles_empty_date():
    parsed = parse_species_row({
        "class_display": "Aves",
        "order": "Passeriformes",
        "scientificName_clean": "Testus birdus",
        "vernacularName": "Test Bird",
        "num_observations": "7",
        "most_recent_date": "",
    })

    assert parsed["most_recent_date"] is None
