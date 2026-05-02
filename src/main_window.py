"""Main application window – tab-based layout."""

from typing import Optional, cast

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QWidget,
)

from src.database import Database
from src.utils.config import WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_TITLE
from src.widgets.dashboard import DashboardWidget
from src.widgets.table_view import TableViewWidget


_GLOBAL_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
}

QTabWidget::pane {
    border: 1px solid #444;
    background: #1e1e2e;
}

QTabBar::tab {
    background: #2d2d44;
    color: #aaa;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background: #3498db;
    color: white;
}

QTabBar::tab:hover:!selected {
    background: #3d3d55;
}

QComboBox {
    background: #2d2d44;
    color: #cdd6f4;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 140px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background: #2d2d44;
    color: #cdd6f4;
    selection-background-color: #3498db;
}

QLineEdit {
    background: #2d2d44;
    color: #cdd6f4;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 8px;
}

QStatusBar {
    background: #181825;
    color: #888;
    font-size: 11px;
}

QLabel {
    color: #cdd6f4;
}
"""


class MainWindow(QMainWindow):
    """Top-level window housing the tab widget."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # database
        self.db = Database()

        # apply global dark theme
        cast(QApplication, QApplication.instance()).setStyleSheet(_GLOBAL_STYLE)

        self._build_ui()
        self._build_menu()
        self._build_statusbar()

    # ── UI ────────────────────────────────────────────────────────────────── #

    def _build_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.dashboard = DashboardWidget(self.db)
        self.table_view = TableViewWidget(self.db)

        self.tabs.addTab(self.dashboard, "📊  Dashboard")
        self.tabs.addTab(self.table_view, "📋  Tabelle")

        self.setCentralWidget(self.tabs)

    def _build_menu(self):
        menu_bar = self.menuBar()
        assert menu_bar is not None

        # Datei
        file_menu = menu_bar.addMenu("&Datei")
        assert file_menu is not None

        refresh_action = QAction("Aktualisieren", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_all)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        quit_action = QAction("Beenden", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Hilfe
        help_menu = menu_bar.addMenu("&Hilfe")
        assert help_menu is not None
        about_action = QAction("Über", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bereit")

    # ── slots ─────────────────────────────────────────────────────────────── #

    def _refresh_all(self):
        self.dashboard.refresh()
        self.table_view.refresh()
        self.status_bar.showMessage("Daten aktualisiert", 3000)

    def _show_about(self):
        QMessageBox.about(
            self,
            "Über Energie-Monitor",
            "<h3>Energie-Monitor</h3>"
            "<p>PyQt6-basierte GUI für Stromdaten aus einer Neon-PostgreSQL-Datenbank.</p>"
            "<p>Zeigt Verbrauch, PV-Erzeugung, Einspeisung und Netzbezug.</p>",
        )

    # ── lifecycle ─────────────────────────────────────────────────────────── #

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        self.db.close()
        super().closeEvent(a0)
