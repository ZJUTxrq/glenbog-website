#!/usr/bin/env python3
import csv
import datetime
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

KML_NS = "http://www.opengis.net/kml/2.2"
BIOCACHE = "https://biocache-ws.ala.org.au/ws"
HEADERS = {"User-Agent": "ala-kml-downloader/1.0"}
PAGE_SIZE = 1000


def parse_kml_polygons(kml_path: Path) -> list:
    tree = ET.parse(kml_path)
    root = tree.getroot()
    polygons = []
    for polygon in root.iter(f"{{{KML_NS}}}Polygon"):
        outer = polygon.find(
            f".//{{{KML_NS}}}outerBoundaryIs"
            f"//{{{KML_NS}}}LinearRing"
            f"//{{{KML_NS}}}coordinates"
        )
        if outer is None or not outer.text:
            continue
        coords = []
        for token in outer.text.strip().split():
            parts = token.split(",")
            if len(parts) >= 2:
                coords.append((float(parts[0]), float(parts[1])))
        if coords:
            polygons.append(coords)
    if not polygons:
        raise ValueError("No Polygon elements found in the KML file.")
    return polygons


def polygons_to_wkt(polygons: list) -> str:
    def ring_wkt(ring):
        return "(" + ", ".join(f"{lon} {lat}" for lon, lat in ring) + ")"
    if len(polygons) == 1:
        return f"POLYGON({ring_wkt(polygons[0])})"
    parts = ", ".join(f"({ring_wkt(r)})" for r in polygons)
    return f"MULTIPOLYGON({parts})"


def _post(url, data: dict, extra_fq: list = None, **kwargs):
    # Build list of tuples to support multiple fq params
    params = [(k, v) for k, v in data.items() if k != 'fq']
    if 'fq' in data and data['fq']:
        params.append(('fq', data['fq']))
    for fq in (extra_fq or []):
        params.append(('fq', fq))
    return requests.post(url, data=params, headers={
        **HEADERS, "Content-Type": "application/x-www-form-urlencoded"
    }, **kwargs)


def _ms_to_iso(ts) -> str:
    try:
        return datetime.datetime.fromtimestamp(
            int(ts) / 1000, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d")
    except Exception:
        return str(ts)


def _flatten(record: dict) -> dict:
    flat = dict(record)
    other = flat.pop("otherProperties", {}) or {}
    flat.update(other)
    if "classs" in flat:
        flat["class"] = flat.pop("classs")
    if "eventDate" in flat and flat["eventDate"] is not None:
        flat["eventDate"] = _ms_to_iso(flat["eventDate"])
    for key in ("recordedBy", "collectors", "collector"):
        if isinstance(flat.get(key), list):
            flat[key] = " | ".join(str(v) for v in flat[key])
    for raw, canon in [
        ("raw_institutionCode", "institutionCode"),
        ("raw_collectionCode", "collectionCode"),
        ("raw_catalogNumber", "catalogNumber"),
        ("raw_occurrenceRemarks", "occurrenceRemarks"),
    ]:
        if not flat.get(canon):
            flat[canon] = flat.pop(raw, "")
        else:
            flat.pop(raw, None)
    if "recordedBy" not in flat and "collector" in flat:
        flat["recordedBy"] = flat["collector"]
    return flat


KINGDOM_FQ = "kingdom:Animalia"


def get_year_facets(wkt: str) -> list:
    url = f"{BIOCACHE}/occurrences/search"
    data = {"q": "*:*", "wkt": wkt, "pageSize": 0,
            "facet": "true", "facets": "year", "flimit": 500}
    resp = _post(url, data, extra_fq=[KINGDOM_FQ], timeout=60)
    resp.raise_for_status()
    body = resp.json()
    for fr in body.get("facetResults", []):
        if fr.get("fieldName") == "year":
            return fr.get("fieldResult", [])
    return []


def _make_year_batches(facets: list, max_per_batch: int = 4000) -> list:
    batches = []
    numeric = [(int(f["label"]), f["count"]) for f in facets if f["label"].isdigit()]
    numeric.sort()
    no_year_count = sum(f["count"] for f in facets if not f["label"].isdigit())
    if no_year_count > 0:
        batches.append(("-year:[* TO *]", no_year_count))
    batch_years, batch_count = [], 0
    for year, count in numeric:
        if batch_years and batch_count + count > max_per_batch:
            lo, hi = batch_years[0], batch_years[-1]
            fq = f"year:{lo}" if lo == hi else f"year:[{lo} TO {hi}]"
            batches.append((fq, batch_count))
            batch_years, batch_count = [], 0
        batch_years.append(year)
        batch_count += count
    if batch_years:
        lo, hi = batch_years[0], batch_years[-1]
        fq = f"year:{lo}" if lo == hi else f"year:[{lo} TO {hi}]"
        batches.append((fq, batch_count))
    return batches


EXTRA_FIELDS = "establishmentMeans,dataGeneralizations,locality,verbatimLocality,samplingProtocol"

def _search_page(wkt, fq, start):
    url = f"{BIOCACHE}/occurrences/search"
    data = {"q": "*:*", "wkt": wkt, "fq": fq, "pageSize": PAGE_SIZE,
            "startIndex": start, "facet": "false", "sort": "id", "dir": "asc",
            "extra": EXTRA_FIELDS}
    resp = _post(url, data, extra_fq=[KINGDOM_FQ], timeout=120)
    resp.raise_for_status()
    body = resp.json()
    return body.get("occurrences", []), body.get("totalRecords", 0)


def download_ala_from_kml(kml_path: Path, output_path: Path, progress: dict = None) -> int:
    polygons = parse_kml_polygons(kml_path)
    wkt = polygons_to_wkt(polygons)

    facets = get_year_facets(wkt)
    total = sum(f["count"] for f in facets)
    batches = _make_year_batches(facets)

    if progress is not None:
        progress.update({"status": "running", "total": total, "fetched": 0,
                         "batches": len(batches), "batch": 0})

    rows_written = 0
    seen_uuids: set = set()
    all_rows: list = []
    all_keys: list = []
    seen_keys: set = set()

    for batch_num, (fq, expected) in enumerate(batches, 1):
        start = 0
        while True:
            records, _ = _search_page(wkt, fq, start)
            if not records:
                break
            for rec in records:
                uid = rec.get("uuid", "")
                if uid and uid in seen_uuids:
                    continue
                if uid:
                    seen_uuids.add(uid)
                flat = _flatten(rec)
                for k in flat:
                    if k not in seen_keys:
                        seen_keys.add(k)
                        all_keys.append(k)
                all_rows.append(flat)
                rows_written += 1
            if progress is not None:
                progress["fetched"] = rows_written
                progress["batch"] = batch_num
            start += PAGE_SIZE
            if start >= expected or len(records) < PAGE_SIZE:
                break
            time.sleep(0.15)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    if progress is not None:
        progress["status"] = "done"
    return rows_written
