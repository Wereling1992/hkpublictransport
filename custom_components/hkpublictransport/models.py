"""Data models for HK Public Transport."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from homeassistant.util import dt as dt_util

from .const import MAX_ARRIVALS


@dataclass
class Arrival:
    """Single upcoming arrival."""

    eta: datetime | None
    minutes_away: int | None
    destination: str | None = None
    is_scheduled: bool = False
    remark: str | None = None
    eta_seq: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for attributes."""
        return {
            "eta": self.eta.isoformat() if self.eta else None,
            "minutes_away": self.minutes_away,
            "destination": self.destination,
            "is_scheduled": self.is_scheduled,
            "remark": self.remark,
        }


@dataclass
class EtaResult:
    """Normalized ETA result for a route + stop combination."""

    operator: str
    route: str
    direction: str | None
    service_type: str | None
    destination: str | None
    stop_id: str
    stop_name: str | None
    stop_seq: int | None
    upcoming_arrivals: list[Arrival] = field(default_factory=list)
    status_reason: str = "ok"
    data_source: str = "live"
    last_updated: datetime = field(default_factory=lambda: dt_util.now())
    remark: str | None = None

    @property
    def next_arrival(self) -> Arrival | None:
        return self.upcoming_arrivals[0] if self.upcoming_arrivals else None

    @property
    def state_minutes(self) -> int | None:
        """Primary sensor state: minutes until next bus (clamped >= 0)."""
        if not self.upcoming_arrivals:
            return None
        minutes = self.upcoming_arrivals[0].minutes_away
        if minutes is None:
            return None
        return max(0, minutes)

    def to_attributes(self) -> dict[str, Any]:
        """Build entity attributes dict."""
        attrs: dict[str, Any] = {
            "route": self.route,
            "operator": self.operator.upper(),
            "direction": self.direction,
            "service_type": self.service_type,
            "destination": self.destination,
            "stop_id": self.stop_id,
            "stop_name": self.stop_name,
            "stop_seq": self.stop_seq,
            "status_reason": self.status_reason,
            "data_source": self.data_source,
            "last_updated": self.last_updated.isoformat(),
            "remark": self.remark,
        }

        if self.upcoming_arrivals:
            attrs["upcoming_arrivals"] = [a.to_dict() for a in self.upcoming_arrivals[:MAX_ARRIVALS]]
            first = self.upcoming_arrivals[0]
            attrs["next_arrival"] = first.eta.isoformat() if first.eta else None
            attrs["is_scheduled"] = first.is_scheduled
            if len(self.upcoming_arrivals) > 1:
                attrs["second_arrival"] = (
                    self.upcoming_arrivals[1].eta.isoformat()
                    if self.upcoming_arrivals[1].eta
                    else None
                )
            if len(self.upcoming_arrivals) > 2:
                attrs["third_arrival"] = (
                    self.upcoming_arrivals[2].eta.isoformat()
                    if self.upcoming_arrivals[2].eta
                    else None
                )
        else:
            attrs["upcoming_arrivals"] = []
            attrs["next_arrival"] = None
            attrs["is_scheduled"] = False

        return attrs


@dataclass
class RouteInfo:
    """Static route information."""

    operator: str
    route: str
    direction: str | None
    service_type: str | None
    origin: str | None
    destination: str | None
    bound: str | None = None  # "O" / "I" style


@dataclass
class StopInfo:
    """Static stop information."""

    stop_id: str
    name_en: str | None
    name_tc: str | None = None
    lat: float | None = None
    long: float | None = None
    operator: str | None = None


def calculate_minutes_away(eta: datetime | None, now: datetime | None = None) -> int | None:
    """Calculate minutes until ETA. Clamp negative/zero to 0."""
    if eta is None:
        return None
    if now is None:
        now = dt_util.now()

    # Ensure both are timezone-aware
    if eta.tzinfo is None:
        eta = eta.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    diff_seconds = (eta - now).total_seconds()
    if diff_seconds <= 0:
        return 0
    return int(diff_seconds // 60)
