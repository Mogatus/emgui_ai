"""Dashboard tab – KPI cards + line chart + bar chart."""

from datetime import datetime, timedelta
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.database import Database
from src.models import MeterReading
from src.widgets.chart_widget import ChartWidget
from src.widgets.kpi_card import KpiCard


# ── background worker ────────────────────────────────────────────────────── #

class _FetchWorker(QThread):
    """Runs the DB query in a background thread so the UI stays responsive."""

    data_ready = pyqtSignal(list)   # list[dict]
    fetch_error = pyqtSignal(str)

    def __init__(self, db: Database, start: Optional[datetime], end: Optional[datetime]):
        super().__init__()
        self.db = db
        self._start_dt = start
        self._end_dt = end

    def run(self):
        try:
            rows = self.db.fetch_data(start=self._start_dt, end=self._end_dt, limit=50000)
            self.data_ready.emit(rows)
        except Exception as exc:
            self.fetch_error.emit(str(exc))


# ── dashboard widget ─────────────────────────────────────────────────────── #

class DashboardWidget(QWidget):
    """Main dashboard with KPI cards, line chart, and bar chart."""

    _RANGES = {
        "Letzte 24 h": 1,
        "Letzte 3 Tage": 3,
        "Letzte 7 Tage": 7,
        "Letzte 30 Tage": 30,
        "Letzte 90 Tage": 90,
    }

    _AUTO_REFRESH_MS = 60_000  # auto-refresh every 60 seconds

    def __init__(self, db: Database, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db = db
        self._worker: Optional[_FetchWorker] = None

        self._build_ui()

        # periodic auto-refresh
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(self._AUTO_REFRESH_MS)

        self.refresh()

    # ── UI construction ──────────────────────────────────────────────────── #

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 8)

        # ── top bar: range selector + refresh ────────────────────────────── #
        top = QHBoxLayout()
        top.addWidget(QLabel("Zeitraum:"))

        self._range_combo = QComboBox()
        self._range_combo.addItems(self._RANGES.keys())
        self._range_combo.setCurrentText("Letzte 7 Tage")
        self._range_combo.currentTextChanged.connect(self.refresh)
        top.addWidget(self._range_combo)

        top.addStretch()

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #888; font-size: 11px;")
        top.addWidget(self._status_label)

        btn_refresh = QPushButton("⟳ Aktualisieren")
        btn_refresh.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; padding: 6px 14px; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        btn_refresh.clicked.connect(self.refresh)
        top.addWidget(btn_refresh)

        root.addLayout(top)

        # ── KPI cards ────────────────────────────────────────────────────── #
        cards = QHBoxLayout()
        self.card_load = KpiCard("Ø Verbrauch", color="#e74c3c")
        self.card_pv = KpiCard("Ø PV-Erzeugung", color="#f1c40f")
        self.card_feed = KpiCard("Ø Einspeisung", color="#2ecc71")
        self.card_purchase = KpiCard("Ø Netzbezug", color="#3498db")
        self.card_autarky = KpiCard("Autarkie", value="–", unit="%", color="#9b59b6")

        for card in (self.card_load, self.card_pv, self.card_feed, self.card_purchase, self.card_autarky):
            cards.addWidget(card)
        root.addLayout(cards)

        # ── charts ───────────────────────────────────────────────────────── #
        self.line_chart = ChartWidget()
        root.addWidget(self.line_chart, stretch=3)

        self.bar_chart = ChartWidget()
        root.addWidget(self.bar_chart, stretch=2)

    # ── data loading ─────────────────────────────────────────────────────── #

    def refresh(self):
        """Trigger an async data fetch."""
        # don't start a new fetch while one is running
        if self._worker is not None and self._worker.isRunning():
            return

        days = self._RANGES.get(self._range_combo.currentText(), 7)
        end = datetime.now()
        start = end - timedelta(days=days)

        self._status_label.setText("Lade Daten …")

        self._worker = _FetchWorker(self.db, start, end)
        self._worker.data_ready.connect(self._on_data)
        self._worker.fetch_error.connect(self._on_error)
        self._worker.start()

    def _on_data(self, raw_rows: list[dict]):
        readings = [MeterReading.from_dict(r) for r in raw_rows]
        self._status_label.setText(f"{len(readings)} Datenpunkte geladen")

        self._update_kpis(readings)
        self.line_chart.plot(readings, title="Energieverlauf")
        self.bar_chart.plot_bar_summary(readings, title="Tagesübersicht (kWh)")

    def _on_error(self, msg: str):
        self._status_label.setText("Fehler!")
        QMessageBox.critical(self, "Datenbankfehler", msg)

    # ── KPI helpers ──────────────────────────────────────────────────────── #

    def _update_kpis(self, readings: list[MeterReading]):
        if not readings:
            for card in (self.card_load, self.card_pv, self.card_feed, self.card_purchase, self.card_autarky):
                card.set_value("–", subtitle="")
            return

        # ── averages over the selected period ────────────────────────────── #
        n = len(readings)
        avg_load = sum(r.loadval or 0 for r in readings) / n
        avg_pv = sum(r.pv or 0 for r in readings) / n
        avg_feed = sum(r.grid_feed_in or 0 for r in readings) / n
        avg_purchase = sum(r.grid_purchase or 0 for r in readings) / n

        # average autarky over period
        total_load = sum(r.loadval or 0 for r in readings)
        total_purchase = sum(r.grid_purchase or 0 for r in readings)
        if total_load > 0:
            avg_autarky = max(0.0, min(100.0, (1 - total_purchase / total_load) * 100))
        else:
            avg_autarky = 100.0

        # ── energy totals (kWh) – assume ~1 reading/min ─────────────────── #
        factor = 1 / 60_000  # W-minutes → kWh
        kwh_load = sum(r.loadval or 0 for r in readings) * factor
        kwh_pv = sum(r.pv or 0 for r in readings) * factor
        kwh_feed = sum(r.grid_feed_in or 0 for r in readings) * factor
        kwh_purchase = sum(r.grid_purchase or 0 for r in readings) * factor

        self.card_load.set_value(f"{avg_load:,.0f}", subtitle=f"Σ {kwh_load:,.1f} kWh")
        self.card_pv.set_value(f"{avg_pv:,.0f}", subtitle=f"Σ {kwh_pv:,.1f} kWh")
        self.card_feed.set_value(f"{avg_feed:,.0f}", subtitle=f"Σ {kwh_feed:,.1f} kWh")
        self.card_purchase.set_value(f"{avg_purchase:,.0f}", subtitle=f"Σ {kwh_purchase:,.1f} kWh")
        self.card_autarky.set_value(f"{avg_autarky:.1f}", subtitle=f"Ø über {n} Werte")
