"""Energie-Monitor – Web GUI (same data as PyQt dashboard)."""

from datetime import datetime, timedelta
from typing import Optional

from flask import Flask, render_template

from src.database import Database
from src.models import MeterReading

app = Flask(__name__)


def _aggregate_period(db: Database, start: datetime, end: datetime) -> dict:
    """Compute KPIs for a period – same logic as PyQt DashboardWidget._update_kpis."""
    rows = db.fetch_data(start=start, end=end, limit=50000)
    readings = [MeterReading.from_dict(r) for r in rows]

    if not readings:
        return {
            "avg_load_w": 0,
            "avg_pv_w": 0,
            "avg_feed_w": 0,
            "avg_purchase_w": 0,
            "autarky_pct": 0.0,
            "kwh_load": 0.0,
            "kwh_pv": 0.0,
            "kwh_feed": 0.0,
            "kwh_purchase": 0.0,
            "num_readings": 0,
        }

    n = len(readings)

    # averages (W)
    avg_load = sum(r.loadval or 0 for r in readings) / n
    avg_pv = sum(r.pv or 0 for r in readings) / n
    avg_feed = sum(r.grid_feed_in or 0 for r in readings) / n
    avg_purchase = sum(r.grid_purchase or 0 for r in readings) / n

    # autarky
    total_load = sum(r.loadval or 0 for r in readings)
    total_purchase = sum(r.grid_purchase or 0 for r in readings)
    if total_load > 0:
        autarky = max(0.0, min(100.0, (1 - total_purchase / total_load) * 100))
    else:
        autarky = 100.0

    # energy totals (kWh) – assume ~1 reading/min
    factor = 1 / 60_000  # W-minutes → kWh
    kwh_load = sum(r.loadval or 0 for r in readings) * factor
    kwh_pv = sum(r.pv or 0 for r in readings) * factor
    kwh_feed = sum(r.grid_feed_in or 0 for r in readings) * factor
    kwh_purchase = sum(r.grid_purchase or 0 for r in readings) * factor

    return {
        "avg_load_w": round(avg_load),
        "avg_pv_w": round(avg_pv),
        "avg_feed_w": round(avg_feed),
        "avg_purchase_w": round(avg_purchase),
        "autarky_pct": round(autarky, 1),
        "kwh_load": round(kwh_load, 1),
        "kwh_pv": round(kwh_pv, 1),
        "kwh_feed": round(kwh_feed, 1),
        "kwh_purchase": round(kwh_purchase, 1),
        "num_readings": n,
    }


@app.route("/")
def index():
    now = datetime.now()
    periods = [
        ("Letzte 24 h", now - timedelta(days=1), now),
        ("Letzte 7 Tage", now - timedelta(days=7), now),
        ("Letzte 30 Tage", now - timedelta(days=30), now),
        ("Aktuelles Jahr", datetime(now.year, 1, 1), now),
    ]

    db = Database()
    try:
        table_data = []
        for label, start, end in periods:
            agg = _aggregate_period(db, start, end)
            agg["label"] = label
            table_data.append(agg)
    finally:
        db.close()

    return render_template("index.html", table_data=table_data, updated=now)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
