"""Reusable chart widget based on matplotlib embedded in PyQt6."""

from datetime import datetime
from typing import Optional

import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from src.models import MeterReading

# colour palette – easy on the eyes
COLORS = {
    "loadval": "#e74c3c",       # red – Verbrauch
    "pv": "#f1c40f",            # yellow – PV
    "grid_feed_in": "#2ecc71",  # green – Einspeisung
    "grid_purchase": "#3498db", # blue  – Netzbezug
}

LABELS = {
    "loadval": "Verbrauch",
    "pv": "PV-Erzeugung",
    "grid_feed_in": "Einspeisung",
    "grid_purchase": "Netzbezug",
}


class ChartWidget(QWidget):
    """Matplotlib-based line chart for meter data."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.figure.set_facecolor("#1e1e2e")
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    # --------------------------------------------------------------------- #

    def plot(
        self,
        readings: list[MeterReading],
        series: Optional[list[str]] = None,
        title: str = "Energieverlauf",
    ):
        """Plot one or more data series.

        Parameters
        ----------
        readings : list[MeterReading]
            Data to plot (must be sorted by timestamp already).
        series : list[str] | None
            Column names to plot.  Defaults to all four.
        title : str
            Chart title.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if series is None:
            series = ["loadval", "pv", "grid_feed_in", "grid_purchase"]

        timestamps = []
        data: dict[str, list] = {s: [] for s in series}

        for r in readings:
            ts = r.timestamp
            if ts is None:
                continue
            timestamps.append(ts)
            for s in series:
                data[s].append(getattr(r, s, 0) or 0)

        if not timestamps:
            ax.set_title("Keine Daten", color="white")
            self._style_axes(ax)
            self.canvas.draw()
            return

        for s in series:
            ax.plot(
                timestamps,
                data[s],
                label=LABELS.get(s, s),
                color=COLORS.get(s, "#ffffff"),
                linewidth=1.2,
                alpha=0.9,
            )

        ax.set_title(title, color="white", fontsize=13, pad=10)
        ax.set_ylabel("Watt", color="white")

        # auto-format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
        self.figure.autofmt_xdate(rotation=30)

        self._style_axes(ax)

        # legend below the chart, outside the plot area
        handles, labels = ax.get_legend_handles_labels()
        self.figure.legend(
            handles, labels,
            loc="lower center",
            ncol=len(labels),
            fontsize=9,
            frameon=False,
            labelcolor="white",
        )
        self.figure.tight_layout(rect=[0, 0.06, 1, 1])
        self.canvas.draw()

    # --------------------------------------------------------------------- #

    def plot_bar_summary(self, readings: list[MeterReading], title: str = "Tagesübersicht"):
        """Stacked bar chart – aggregated per day (kWh)."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # aggregate per day
        daily: dict[str, dict[str, float]] = {}
        for r in readings:
            ts = r.timestamp
            if ts is None:
                continue
            day = ts.strftime("%Y-%m-%d")
            if day not in daily:
                daily[day] = {"loadval": 0, "pv": 0, "grid_feed_in": 0, "grid_purchase": 0}
            # assume each reading ≈ 1-minute interval → /60000 for kWh
            daily[day]["loadval"] += (r.loadval or 0)
            daily[day]["pv"] += (r.pv or 0)
            daily[day]["grid_feed_in"] += (r.grid_feed_in or 0)
            daily[day]["grid_purchase"] += (r.grid_purchase or 0)

        if not daily:
            ax.set_title("Keine Daten", color="white")
            self._style_axes(ax)
            self.canvas.draw()
            return

        days = sorted(daily.keys())
        # rough conversion: sum of W values * interval_minutes / 60 / 1000
        # without knowing exact interval we just show raw sums scaled
        factor = 1 / 60000  # W-minutes → kWh approx (1 reading/min)
        x_labels = [d[5:] for d in days]  # MM-DD
        x_range = range(len(days))

        for key in ["loadval", "pv", "grid_feed_in", "grid_purchase"]:
            vals = [daily[d][key] * factor for d in days]
            ax.bar(
                x_range,
                vals,
                label=LABELS[key],
                color=COLORS[key],
                alpha=0.8,
                width=0.6,
            )

        ax.set_xticks(list(x_range))
        ax.set_xticklabels(x_labels, rotation=45, fontsize=8)
        ax.set_title(title, color="white", fontsize=13, pad=10)
        ax.set_ylabel("kWh (ca.)", color="white")

        self._style_axes(ax)

        # legend below the chart, outside the plot area
        handles, labels = ax.get_legend_handles_labels()
        self.figure.legend(
            handles, labels,
            loc="lower center",
            ncol=len(labels),
            fontsize=9,
            frameon=False,
            labelcolor="white",
        )
        self.figure.tight_layout(rect=[0, 0.08, 1, 1])
        self.canvas.draw()

    # --------------------------------------------------------------------- #

    @staticmethod
    def _style_axes(ax):
        """Apply dark-theme styling to axes."""
        ax.set_facecolor("#2d2d44")
        ax.tick_params(colors="white", labelsize=8)
        ax.spines["bottom"].set_color("#555")
        ax.spines["left"].set_color("#555")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.15, color="white")
