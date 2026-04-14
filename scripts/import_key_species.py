"""
Import key species data from key_species.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_key_species.py
"""

import csv
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from glenbog.extensions import db
from glenbog.models import KeySpecies

KEY_SPECIES_CSV = '/data/key_species.csv'


def import_key_species(csv_path: str) -> None:
    KeySpecies.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            most_recent = None
            if row['most_recent_date']:
                most_recent = date.fromisoformat(row['most_recent_date'])
            db.session.add(KeySpecies(
                class_display=row['class'],
                common_name=row['common_name'],
                scientific_name=row['scientific_name'],
                num_observations=int(row['num_observations']),
                most_recent_date=most_recent,
            ))
            count += 1

    db.session.commit()
    print(f'Imported {count} key species records.')


if __name__ == '__main__':
    with app.app_context():
        import_key_species(KEY_SPECIES_CSV)
