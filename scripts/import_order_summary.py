"""
Import order summary data from Order_Summary.csv into PostgreSQL.

Usage (inside the app container):
    python scripts/import_order_summary.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from glenbog.extensions import db
from glenbog.models import OrderSummary

CSV_PATH = f"{os.environ.get('DATA_DIR', '/data')}/Order_Summary.csv"


def import_order_summary(csv_path: str) -> None:
    OrderSummary.__table__.drop(db.engine, checkfirst=True)
    db.create_all()

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            db.session.add(OrderSummary(
                order=row['order'],
                class_display=row['class'],
                total_species=int(row['total_species']),
                total_observations=int(row['total_observations']),
                proportion=float(row['proportion']),
                order_description=row['order_description'] or None,
            ))
            count += 1

    db.session.commit()
    print(f'Imported {count} order summary records.')


if __name__ == '__main__':
    with app.app_context():
        import_order_summary(CSV_PATH)
