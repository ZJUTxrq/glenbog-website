from datetime import date

from scripts.import_key_species import parse_key_species_row


def test_parse_key_species_row_converts_values():
    parsed = parse_key_species_row({
        "class": "Aves",
        "common_name": "Test Bird",
        "scientific_name": "Testus birdus",
        "num_observations": "5",
        "most_recent_date": "2026-04-01",
    })

    assert parsed["class_display"] == "Aves"
    assert parsed["num_observations"] == 5
    assert parsed["most_recent_date"] == date(2026, 4, 1)
