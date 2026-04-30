"""
Import survey map data from SurveyMap_Past6Months_Glenbog.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_survey_map.py
"""

import csv
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from glenbog.extensions import db
from glenbog.models import SurveyObservation

CSV_PATH = f"{os.environ.get('DATA_DIR', '/data')}/SurveyMap_Past6Months.csv"


def import_survey_map(csv_path: str) -> None:
    SurveyObservation.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if not row['decimalLatitude'] or not row['decimalLongitude']:
                continue
            event_date = date.fromisoformat(row['eventDate'])
            db.session.add(SurveyObservation(
                scientific_name=row['scientificName'],
                vernacular_name=row['vernacularName'],
                event_date=event_date,
                data_resource_name=row['dataResourceName'],
                recorded_by=row.get('recordedBy'),
                latitude=float(row['decimalLatitude']),
                longitude=float(row['decimalLongitude']),
            ))
            count += 1

    db.session.commit()
    print(f'Imported {count} survey observation records.')


if __name__ == '__main__':
    with app.app_context():
        import_survey_map(CSV_PATH)
