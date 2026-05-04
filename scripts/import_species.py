"""
Import species data from species_summary.csv into the PostgreSQL database.

Usage (inside the app container):
    python import_species.py
    python import_species.py /path/to/Species_Summary.csv
"""

import csv
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_data_dir = os.environ.get('DATA_DIR', '/data')
CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else f'{_data_dir}/Species_Summary.csv'


def parse_species_row(row: dict) -> dict:
    most_recent = None
    if row['most_recent_date']:
        most_recent = date.fromisoformat(row['most_recent_date'])

    return {
        'class_display': row['class_display'],
        'order': row['order'],
        'scientific_name': row['scientificName_clean'],
        'vernacular_name': row['vernacularName'],
        'num_observations': int(row['num_observations']),
        'most_recent_date': most_recent,
    }


def import_species(csv_path: str) -> None:
    from app import app
    from glenbog.extensions import db
    from glenbog.models import Species

    with app.app_context():
        from glenbog.models import Species as SpeciesModel
        SpeciesModel.__table__.drop(db.engine, checkfirst=True)
        db.create_all()

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # Skip if already imported (avoid duplicates)
                existing = Species.query.filter_by(
                    scientific_name=row['scientificName_clean']
                ).first()
                if existing:
                    continue
                db.session.add(Species(**parse_species_row(row)))
                count += 1

            db.session.commit()
            print(f'Imported {count} species records.')


if __name__ == '__main__':
    import_species(CSV_PATH)
