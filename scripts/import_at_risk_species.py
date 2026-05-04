"""
Import at-risk species data from At_Risk_Species.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_at_risk_species.py
"""

import csv
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CSV_PATH = f"{os.environ.get('DATA_DIR', '/data')}/At_Risk_Species.csv"


def parse_at_risk_species_row(row: dict) -> dict:
    obs_date = None
    if row['most_recent_observation']:
        obs_date = date.fromisoformat(row['most_recent_observation'])

    return {
        'scientific_name': row['scientificName'],
        'common_name': row['vernacularName'],
        'class_display': row['class'],
        'order': row['order'],
        'num_observations': int(float(row['number_of_observations'])),
        'date_of_observation': obs_date,
        'status': row['at_risk_status'],
        'latitude': float(row['decimalLatitude']) if row['decimalLatitude'] else None,
        'longitude': float(row['decimalLongitude']) if row['decimalLongitude'] else None,
    }


def import_at_risk_species(csv_path: str) -> None:
    from glenbog.extensions import db
    from glenbog.models import AtRiskSpecies

    AtRiskSpecies.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            db.session.add(AtRiskSpecies(**parse_at_risk_species_row(row)))
            count += 1

    db.session.commit()
    print(f'Imported {count} at-risk species records.')


if __name__ == '__main__':
    from app import app

    with app.app_context():
        import_at_risk_species(CSV_PATH)
