from scripts.import_order_summary import parse_order_summary_row


def test_parse_order_summary_row_converts_values():
    parsed = parse_order_summary_row({
        "order": "Passeriformes",
        "class": "Aves",
        "total_species": "3",
        "total_observations": "21",
        "proportion": "0.75",
        "order_description": "",
    })

    assert parsed == {
        "order": "Passeriformes",
        "class_display": "Aves",
        "total_species": 3,
        "total_observations": 21,
        "proportion": 0.75,
        "order_description": None,
    }
