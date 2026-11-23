"""DataUpdateCoordinator for HK Public Transport."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ETA_CACHE_TTL,
    STATUS_CACHED,
    STATUS_OK,
)
from .models import EtaResult
from .providers import ProviderHub

_LOGGER = logging.getLogger(__name__)


class HkBusEtaCoordinator(DataUpdateCoordinator[EtaResult]):
    """Coordinator that fetches ETA for one monitored target."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        hub: ProviderHub,
    ) -> None:
        self.entry = entry
        self.hub = hub
        self._last_good: EtaResult | None = None
        self._last_good_ts: datetime | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    @property
    def config(self) -> dict[str, Any]:
        return self.entry.data

    async def _async_update_data(self) -> EtaResult:
        """Fetch latest ETA from the appropriate provider."""
        cfg = self.config
        operator = cfg.get("operator", "kmb")
        route = cfg["route"]
        stop_id = cfg["stop_id"]
        direction = cfg.get("direction")
        service_type = cfg.get("service_type", "1")
        stop_name = cfg.get("stop_name")
        destination = cfg.get("destination")
        stop_seq = cfg.get("stop_seq")

        try:
            result = await self.hub.fetch_eta(
                operator=operator,
                stop_id=stop_id,
                route=route,
                direction=direction,
                service_type=service_type,
                stop_name=stop_name,
                destination=destination,
                stop_seq=stop_seq,
            )
        except Exception as err:
            _LOGGER.warning("ETA update failed for %s %s: %s", route, stop_id, err)
            # Serve cached if still fresh
            if self._last_good and self._last_good_ts:
                age = dt_util.now() - self._last_good_ts
                if age < ETA_CACHE_TTL * 3:  # allow a bit longer on error
                    cached = self._last_good
                    cached.status_reason = STATUS_CACHED
                    cached.data_source = "cache"
                    return cached
            raise UpdateFailed(f"Error fetching ETA: {err}") from err

        if result.status_reason in (STATUS_OK, "no_service"):
            self._last_good = result
            self._last_good_ts = dt_util.now()
        elif self._last_good and self._last_good_ts:
            age = dt_util.now() - self._last_good_ts
            if age < ETA_CACHE_TTL * 2:
                cached = self._last_good
                cached.status_reason = STATUS_CACHED
                cached.data_source = "cache"
                return cached

        return result
