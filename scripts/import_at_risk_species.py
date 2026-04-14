"""
Import at-risk species data from At_Risk_Species_Glenbog.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_at_risk_species.py
"""

import csv
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from glenbog.extensions import db
from glenbog.models import AtRiskSpecies

CSV_PATH = '/data/At_Risk_Species_Glenbog.csv'


def import_at_risk_species(csv_path: str) -> None:
    AtRiskSpecies.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            obs_date = None
            if row['Date of Observation']:
                obs_date = date.fromisoformat(row['Date of Observation'])

            db.session.add(AtRiskSpecies(
                scientific_name=row['Scientific Name'],
                common_name=row['Common Name'],
                class_display=row['Class'],
                order=row['Order'],
                num_observations=int(float(row['No. of Observations'])),
                date_of_observation=obs_date,
                status=row['Status'],
                latitude=float(row['Decimal Latitude']) if row['Decimal Latitude'] else None,
                longitude=float(row['Decimal Longitude']) if row['Decimal Longitude'] else None,
            ))
            count += 1

    db.session.commit()
    print(f'Imported {count} at-risk species records.')


if __name__ == '__main__':
    with app.app_context():
        import_at_risk_species(CSV_PATH)
