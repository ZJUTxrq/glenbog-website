"""
Import class summary data from class_summary.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_class_summary.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from glenbog.extensions import db
from glenbog.models import SpeciesClassSummary

CLASS_CSV = '/data/Class_Summary.csv'


def import_class_summary(csv_path: str) -> None:
    SpeciesClassSummary.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if row['class_display'] == 'Grand Total':
                continue
            db.session.add(SpeciesClassSummary(
                class_display=row['class_display'],
                num_observations=int(row['num_observations']),
                num_species=int(row['num_species']),
                class_description=row['class_description'] or None,
            ))
            count += 1

    db.session.commit()
    print(f'Imported {count} class summary records.')


if __name__ == '__main__':
    with app.app_context():
        import_class_summary(CLASS_CSV)
