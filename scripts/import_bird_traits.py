"""
Import bird traits data from Bird_Traits.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_bird_traits.py
"""

import csv
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from glenbog.extensions import db
from glenbog.models import BirdTrait

CSV_PATH = f"{os.environ.get('DATA_DIR', '/data')}/Bird_Traits.csv"


def import_bird_traits(csv_path: str) -> None:
    BirdTrait.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            most_recent = None
            if row['most_recent_date']:
                most_recent = date.fromisoformat(row['most_recent_date'])

            db.session.add(BirdTrait(
                scientific_name=row['scientific_name'],
                common_name=row['common_name'],
                most_recent_date=most_recent,
                iucn_status=row['iucn_status'] or None,
                primary_habitat=row['primary_habitat'] or None,
                primary_diet=row['primary_diet'] or None,
                average_mass_g=float(row['average_mass_g']) if row['average_mass_g'] else None,
                migratory=row['migratory'] or None,
            ))
            count += 1

    db.session.commit()
    print(f'Imported {count} bird trait records.')


if __name__ == '__main__':
    with app.app_context():
        import_bird_traits(CSV_PATH)
