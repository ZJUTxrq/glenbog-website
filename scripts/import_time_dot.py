"""
Import time dot graph data from TimeDotGraph_Data_Glenbog.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_time_dot.py
"""

import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from glenbog.extensions import db
from glenbog.models import TimeDotObservation

CSV_PATH = f"{os.environ.get('DATA_DIR', '/data')}/TimeDotGraph_Data.csv"


def import_time_dot(csv_path: str) -> None:
    TimeDotObservation.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if not row['eventDate']:
                continue
            event_date = datetime.strptime(row['eventDate'], '%Y-%m-%d').date()
            db.session.add(TimeDotObservation(
                scientific_name=row['scientificName'],
                vernacular_name=row['vernacularName'],
                class_display=row.get('class', ''),
                order=row.get('order', ''),
                family=row.get('family', ''),
                event_date=event_date,
            ))
            count += 1

    db.session.commit()
    print(f'Imported {count} time dot observation records.')


if __name__ == '__main__':
    with app.app_context():
        import_time_dot(CSV_PATH)
