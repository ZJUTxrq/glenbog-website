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

CSV_PATH = f"{os.environ.get('DATA_DIR', '/data')}/TimeDotGraph_Data.csv"


def parse_time_dot_row(row: dict) -> dict | None:
    if not row['eventDate']:
        return None

    return {
        'scientific_name': row['scientificName'],
        'vernacular_name': row['vernacularName'],
        'class_display': row.get('class', ''),
        'order': row.get('order', ''),
        'family': row.get('family', ''),
        'event_date': datetime.strptime(row['eventDate'], '%Y-%m-%d').date(),
    }


def import_time_dot(csv_path: str) -> None:
    from glenbog.extensions import db
    from glenbog.models import TimeDotObservation

    TimeDotObservation.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            parsed = parse_time_dot_row(row)
            if parsed is None:
                continue
            db.session.add(TimeDotObservation(**parsed))
            count += 1

    db.session.commit()
    print(f'Imported {count} time dot observation records.')


if __name__ == '__main__':
    from app import app

    with app.app_context():
        import_time_dot(CSV_PATH)
