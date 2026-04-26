"""Data models for meter readings."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MeterReading:
    """Single row from the meter_data table."""
    id: int
    loadval: Optional[int]       # Verbrauch (W)
    pv: Optional[int]            # PV-Erzeugung (W)
    grid_feed_in: Optional[int]  # Einspeisung (W)
    grid_purchase: Optional[int] # Netzbezug (W)
    savetimestamp: str            # Zeitstempel als String

    @property
    def timestamp(self) -> Optional[datetime]:
        """Try to parse savetimestamp into a datetime object."""
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%d.%m.%Y %H:%M:%S",
            "%d.%m.%Y %H:%M",
        ):
            try:
                return datetime.strptime(self.savetimestamp, fmt)
            except ValueError:
                continue
        return None

    @property
    def self_consumption(self) -> int:
        """Eigenverbrauch = PV - Einspeisung (clamped to >= 0)."""
        pv = self.pv or 0
        feed = self.grid_feed_in or 0
        return max(pv - feed, 0)

    @property
    def autarky(self) -> float:
        """Autarkiegrad in % (0-100)."""
        load = self.loadval or 0
        purchase = self.grid_purchase or 0
        if load == 0:
            return 100.0
        return max(0.0, min(100.0, (1 - purchase / load) * 100))

    @classmethod
    def from_dict(cls, d: dict) -> "MeterReading":
        return cls(
            id=d["id"],
            loadval=d.get("loadval"),
            pv=d.get("pv"),
            grid_feed_in=d.get("grid_feed_in"),
            grid_purchase=d.get("grid_purchase"),
            savetimestamp=d.get("savetimestamp", ""),
        )
