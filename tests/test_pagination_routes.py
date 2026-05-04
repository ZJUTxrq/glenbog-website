from glenbog.extensions import db
from glenbog.models import AtRiskSpecies, BirdTrait, KeySpecies, OrderSummary, Species


def test_species_paginates_six_items_per_page(app, logged_in_client):
    with app.app_context():
        for i in range(7):
            db.session.add(Species(
                class_display="Aves",
                order="Passeriformes",
                scientific_name=f"Species {i:02d}",
                vernacular_name=f"Bird {i:02d}",
                num_observations=i,
            ))
        db.session.commit()

    page_one = logged_in_client.get("/species?page=1")
    page_two = logged_in_client.get("/species?page=2")

    assert page_one.status_code == 200
    assert b"Bird 00" in page_one.data
    assert b"Bird 06" not in page_one.data
    assert page_two.status_code == 200
    assert b"Bird 06" in page_two.data
    assert b"Bird 00" not in page_two.data


def test_at_risk_species_paginates_six_items_per_page(app, logged_in_client):
    with app.app_context():
        for i in range(7):
            db.session.add(AtRiskSpecies(
                scientific_name=f"At Risk Species {i:02d}",
                common_name=f"At Risk Bird {i:02d}",
                class_display="Aves",
                order="Passeriformes",
                num_observations=i,
                status="Endangered",
            ))
        db.session.commit()

    page_one = logged_in_client.get("/species/at-risk?page=1")
    page_two = logged_in_client.get("/species/at-risk?page=2")

    assert page_one.status_code == 200
    assert b"At Risk Bird 00" in page_one.data
    assert b"At Risk Bird 06" not in page_one.data
    assert page_two.status_code == 200
    assert b"At Risk Bird 06" in page_two.data


def test_key_species_paginates_six_items_per_page(app, logged_in_client):
    with app.app_context():
        for i in range(7):
            db.session.add(KeySpecies(
                class_display="Aves",
                common_name=f"Key Bird {i:02d}",
                scientific_name=f"Key Species {i:02d}",
                num_observations=i,
            ))
        db.session.commit()

    page_one = logged_in_client.get("/species/key?page=1")
    page_two = logged_in_client.get("/species/key?page=2")

    assert page_one.status_code == 200
    assert b"Key Bird 00" in page_one.data
    assert b"Key Bird 06" not in page_one.data
    assert page_two.status_code == 200
    assert b"Key Bird 06" in page_two.data


def test_order_summary_paginates_six_items_per_page(app, logged_in_client):
    with app.app_context():
        for i in range(7):
            db.session.add(OrderSummary(
                order=f"Order {i:02d}",
                class_display="Aves",
                total_species=i + 1,
                total_observations=100 - i,
                proportion=0.1,
            ))
        db.session.commit()

    page_one = logged_in_client.get("/order-summary?page=1")
    page_two = logged_in_client.get("/order-summary?page=2")

    assert page_one.status_code == 200
    assert b"Order 00" in page_one.data
    assert b"Order 06" not in page_one.data
    assert page_two.status_code == 200
    assert b"Order 06" in page_two.data


def test_bird_traits_paginates_six_items_per_page(app, logged_in_client):
    with app.app_context():
        for i in range(7):
            db.session.add(BirdTrait(
                scientific_name=f"Trait Species {i:02d}",
                common_name=f"Trait Bird {i:02d}",
                iucn_status="LC",
            ))
        db.session.commit()

    page_one = logged_in_client.get("/bird-traits?page=1")
    page_two = logged_in_client.get("/bird-traits?page=2")

    assert page_one.status_code == 200
    assert b"Trait Bird 00" in page_one.data
    assert b"Trait Bird 06" not in page_one.data
    assert page_two.status_code == 200
    assert b"Trait Bird 06" in page_two.data
