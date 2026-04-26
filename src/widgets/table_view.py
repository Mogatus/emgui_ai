"""Table view – sortable, searchable table of raw meter data."""

from datetime import datetime, timedelta
from typing import Optional

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.database import Database
from src.models import MeterReading


# ── table model ──────────────────────────────────────────────────────────── #

_COLUMNS = ["Zeitstempel", "Verbrauch (W)", "PV (W)", "Einspeisung (W)", "Netzbezug (W)", "Autarkie (%)"]


class _MeterTableModel(QAbstractTableModel):
    def __init__(self, readings: list[MeterReading] | None = None):
        super().__init__()
        self._data: list[MeterReading] = readings or []

    def set_data(self, readings: list[MeterReading]):
        self.beginResetModel()
        self._data = readings
        self.endResetModel()

    # -- required overrides ------------------------------------------------

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(_COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return r.savetimestamp
            if col == 1:
                return str(r.loadval or 0)
            if col == 2:
                return str(r.pv or 0)
            if col == 3:
                return str(r.grid_feed_in or 0)
            if col == 4:
                return str(r.grid_purchase or 0)
            if col == 5:
                return f"{r.autarky:.1f}"

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col >= 1:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 5:
                val = r.autarky
                if val >= 80:
                    return QColor("#2ecc71")
                if val >= 50:
                    return QColor("#f1c40f")
                return QColor("#e74c3c")

        return None


# ── worker ────────────────────────────────────────────────────────────────── #

class _FetchWorker(QThread):
    data_ready = pyqtSignal(list)
    fetch_error = pyqtSignal(str)

    def __init__(self, db: Database, start, end, limit):
        super().__init__()
        self.db = db
        self._start_dt = start
        self._end_dt = end
        self._limit = limit

    def run(self):
        try:
            self.data_ready.emit(self.db.fetch_data(self._start_dt, self._end_dt, self._limit))
        except Exception as e:
            self.fetch_error.emit(str(e))


# ── widget ────────────────────────────────────────────────────────────────── #

class TableViewWidget(QWidget):
    """Full-featured table view of meter data with sort & filter."""

    _RANGES = {
        "Letzte 24 h": 1,
        "Letzte 3 Tage": 3,
        "Letzte 7 Tage": 7,
        "Letzte 30 Tage": 30,
    }

    def __init__(self, db: Database, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db = db
        self._worker: Optional[_FetchWorker] = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 8)

        # toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Zeitraum:"))

        self._range_combo = QComboBox()
        self._range_combo.addItems(self._RANGES.keys())
        self._range_combo.setCurrentText("Letzte 7 Tage")
        self._range_combo.currentTextChanged.connect(self.refresh)
        toolbar.addWidget(self._range_combo)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Suche …")
        self._filter_edit.setMaximumWidth(220)
        self._filter_edit.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self._filter_edit)

        self._status = QLabel("")
        self._status.setStyleSheet("color:#888; font-size:11px;")
        toolbar.addWidget(self._status)

        btn = QPushButton("⟳")
        btn.setFixedWidth(36)
        btn.setStyleSheet(
            "QPushButton{background:#3498db;color:white;border-radius:4px;padding:4px;}"
            "QPushButton:hover{background:#2980b9;}"
        )
        btn.clicked.connect(self.refresh)
        toolbar.addWidget(btn)

        root.addLayout(toolbar)

        # table
        self._model = _MeterTableModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)  # filter all columns

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setStyleSheet(
            """
            QTableView {
                background-color: #1e1e2e;
                alternate-background-color: #252540;
                color: #ddd;
                gridline-color: #444;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #2d2d44;
                color: #ccc;
                padding: 4px;
                border: 1px solid #444;
                font-weight: bold;
            }
            """
        )
        root.addWidget(self._table)

    def _apply_filter(self, text: str):
        self._proxy.setFilterFixedString(text)

    def refresh(self):
        # don't start a new fetch while one is running
        if self._worker is not None and self._worker.isRunning():
            return

        days = self._RANGES.get(self._range_combo.currentText(), 7)
        end = datetime.now()
        start = end - timedelta(days=days)
        self._status.setText("Lade …")

        self._worker = _FetchWorker(self.db, start, end, 20000)
        self._worker.data_ready.connect(self._on_data)
        self._worker.fetch_error.connect(self._on_error)
        self._worker.start()

    def _on_data(self, rows: list[dict]):
        readings = [MeterReading.from_dict(r) for r in rows]
        self._model.set_data(readings)
        self._status.setText(f"{len(readings)} Zeilen")

    def _on_error(self, msg: str):
        self._status.setText("Fehler")
        QMessageBox.critical(self, "Datenbankfehler", msg)
