"""Live-tile / KPI cards for the dashboard."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class KpiCard(QFrame):
    """Small card that shows a single KPI value with title and unit."""

    def __init__(
        self,
        title: str,
        value: str = "–",
        unit: str = "W",
        color: str = "#3498db",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"""
            KpiCard {{
                background-color: #2d2d44;
                border: 1px solid {color};
                border-radius: 10px;
                padding: 12px;
            }}
            """
        )
        self.setMinimumSize(160, 100)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._title_label = QLabel(title)
        self._title_label.setFont(QFont("Segoe UI", 10))
        self._title_label.setStyleSheet("color: #aaa;")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {color};")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._unit_label = QLabel(unit)
        self._unit_label.setFont(QFont("Segoe UI", 9))
        self._unit_label.setStyleSheet("color: #888;")
        self._unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sub_label = QLabel("")
        self._sub_label.setFont(QFont("Segoe UI", 8))
        self._sub_label.setStyleSheet("color: #666;")
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)
        layout.addWidget(self._unit_label)
        layout.addWidget(self._sub_label)

    def set_value(self, value: str, unit: str | None = None, subtitle: str = ""):
        self._value_label.setText(value)
        if unit is not None:
            self._unit_label.setText(unit)
        self._sub_label.setText(subtitle)
