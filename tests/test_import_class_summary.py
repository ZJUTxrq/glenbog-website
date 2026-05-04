from scripts.import_class_summary import parse_class_summary_row


def test_parse_class_summary_row_converts_values():
    parsed = parse_class_summary_row({
        "class_display": "Aves",
        "num_observations": "12",
        "num_species": "4",
        "class_description": "Birds",
    })

    assert parsed == {
        "class_display": "Aves",
        "num_observations": 12,
        "num_species": 4,
        "class_description": "Birds",
    }


def test_parse_class_summary_row_skips_grand_total():
    assert parse_class_summary_row({
        "class_display": "Grand Total",
        "num_observations": "12",
        "num_species": "4",
        "class_description": "",
    }) is None
