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

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QToolTip, QWidget, QVBoxLayout

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

        # tooltip state
        self._daily_data: dict[str, dict[str, float]] = {}
        self._daily_count: dict[str, int] = {}
        self._tick_labels: list[str] = []   # display labels (MM-DD)
        self._tick_days: list[str] = []     # full date keys (YYYY-MM-DD)
        self._hover_cid: int | None = None

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
        """Grouped bar chart – average Watt per day."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # aggregate per day: sum + count for average
        daily: dict[str, dict[str, float]] = {}
        daily_count: dict[str, int] = {}
        for r in readings:
            ts = r.timestamp
            if ts is None:
                continue
            day = ts.strftime("%Y-%m-%d")
            if day not in daily:
                daily[day] = {"loadval": 0, "pv": 0, "grid_feed_in": 0, "grid_purchase": 0}
                daily_count[day] = 0
            daily[day]["loadval"] += (r.loadval or 0)
            daily[day]["pv"] += (r.pv or 0)
            daily[day]["grid_feed_in"] += (r.grid_feed_in or 0)
            daily[day]["grid_purchase"] += (r.grid_purchase or 0)
            daily_count[day] += 1

        if not daily:
            ax.set_title("Keine Daten", color="white")
            self._style_axes(ax)
            self.canvas.draw()
            return

        days = sorted(daily.keys())
        x_labels = [d[5:] for d in days]  # MM-DD

        keys = ["loadval", "pv", "grid_feed_in", "grid_purchase"]
        n_keys = len(keys)
        bar_width = 0.8 / n_keys  # total group width ≈ 0.8

        import numpy as np
        x = np.arange(len(days))

        for i, key in enumerate(keys):
            # average Watt per day
            vals = [daily[d][key] / daily_count[d] for d in days]
            offset = (i - (n_keys - 1) / 2) * bar_width
            ax.bar(
                x + offset,
                vals,
                label=LABELS[key],
                color=COLORS[key],
                alpha=0.85,
                width=bar_width,
            )

        ax.set_xticks(list(x))
        ax.set_xticklabels(x_labels, rotation=45, fontsize=8)
        ax.set_title(title, color="white", fontsize=13, pad=10)
        ax.set_ylabel("Watt (Ø)", color="white")

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

        # store daily data for tooltips
        self._daily_data = daily
        self._daily_count = daily_count
        self._tick_labels = x_labels
        self._tick_days = days

        # connect hover event (disconnect previous if any)
        if self._hover_cid is not None:
            self.canvas.mpl_disconnect(self._hover_cid)
        self._hover_cid = self.canvas.mpl_connect("motion_notify_event", self._on_bar_hover)

        self.canvas.draw()

    # ── tooltip on x-tick hover ──────────────────────────────────────────── #

    def _on_bar_hover(self, event):
        """Show a QToolTip with raw day data when hovering near an x-tick label."""
        if event.inaxes is None and event.x is not None and event.y is not None:
            # user is in the margin area (where tick labels live)
            ax = self.figure.axes[0] if self.figure.axes else None
            if ax is None:
                return
            # find the closest tick by x pixel coordinate
            best_idx = None
            best_dist = float("inf")
            for idx, tick in enumerate(ax.get_xticklabels()):
                bbox = tick.get_window_extent(self.canvas.get_renderer())
                cx = (bbox.x0 + bbox.x1) / 2
                cy = (bbox.y0 + bbox.y1) / 2
                dist = ((event.x - cx) ** 2 + (event.y - cy) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_idx = idx

            # only show if cursor is reasonably close (within 30 px)
            if best_idx is not None and best_dist < 30 and best_idx < len(self._tick_days):
                day_key = self._tick_days[best_idx]
                d = self._daily_data.get(day_key)
                cnt = self._daily_count.get(day_key, 1)
                if d:
                    tip = (
                        f"📅 {day_key}\n"
                        f"{'─' * 28}\n"
                        f"Verbrauch:   Ø {d['loadval']/cnt:,.0f} W  (Σ {d['loadval']:,.0f} W)\n"
                        f"PV:          Ø {d['pv']/cnt:,.0f} W  (Σ {d['pv']:,.0f} W)\n"
                        f"Einspeisung: Ø {d['grid_feed_in']/cnt:,.0f} W  (Σ {d['grid_feed_in']:,.0f} W)\n"
                        f"Netzbezug:   Ø {d['grid_purchase']/cnt:,.0f} W  (Σ {d['grid_purchase']:,.0f} W)\n"
                        f"{'─' * 28}\n"
                        f"Datenpunkte: {cnt}"
                    )
                    global_pos = self.canvas.mapToGlobal(QPoint(int(event.x), int(self.canvas.height() - event.y)))
                    QToolTip.showText(global_pos, tip, self.canvas)
                    return

        QToolTip.hideText()

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
