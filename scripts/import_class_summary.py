"""
Import class summary data from class_summary.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_class_summary.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CLASS_CSV = f"{os.environ.get('DATA_DIR', '/data')}/Class_Summary.csv"


def parse_class_summary_row(row: dict) -> dict | None:
    if row['class_display'] == 'Grand Total':
        return None

    return {
        'class_display': row['class_display'],
        'num_observations': int(row['num_observations']),
        'num_species': int(row['num_species']),
        'class_description': row['class_description'] or None,
    }


def import_class_summary(csv_path: str) -> None:
    from glenbog.extensions import db
    from glenbog.models import SpeciesClassSummary

    SpeciesClassSummary.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            parsed = parse_class_summary_row(row)
            if parsed is None:
                continue
            db.session.add(SpeciesClassSummary(**parsed))
            count += 1

    db.session.commit()
    print(f'Imported {count} class summary records.')


if __name__ == '__main__':
    from app import app

    with app.app_context():
        import_class_summary(CLASS_CSV)
