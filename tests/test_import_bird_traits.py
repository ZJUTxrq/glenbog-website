from datetime import date

from scripts.import_bird_traits import parse_bird_traits_row


def test_parse_bird_traits_row_converts_values():
    parsed = parse_bird_traits_row({
        "scientific_name": "Testus birdus",
        "common_name": "Test Bird",
        "most_recent_date": "2026-04-01",
        "iucn_status": "EN",
        "primary_habitat": "Forest",
        "primary_diet": "Insects",
        "average_mass_g": "12.5",
        "migratory": "Resident",
    })

    assert parsed["most_recent_date"] == date(2026, 4, 1)
    assert parsed["average_mass_g"] == 12.5
    assert parsed["iucn_status"] == "EN"


def test_parse_bird_traits_row_handles_empty_optional_values():
    parsed = parse_bird_traits_row({
        "scientific_name": "Testus birdus",
        "common_name": "Test Bird",
        "most_recent_date": "",
        "iucn_status": "",
        "primary_habitat": "",
        "primary_diet": "",
        "average_mass_g": "",
        "migratory": "",
    })

    assert parsed["most_recent_date"] is None
    assert parsed["iucn_status"] is None
    assert parsed["primary_habitat"] is None
    assert parsed["primary_diet"] is None
    assert parsed["average_mass_g"] is None
    assert parsed["migratory"] is None
