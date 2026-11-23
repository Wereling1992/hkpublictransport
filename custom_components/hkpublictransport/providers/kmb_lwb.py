"""KMB and LWB provider using official data.etabus.gov.hk APIs."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import aiohttp
from homeassistant.util import dt as dt_util

from ..const import (
    KMB_API_BASE,
    OPERATOR_KMB,
    OPERATOR_LWB,
    REQUEST_TIMEOUT,
    STATUS_API_ERROR,
    STATUS_API_TIMEOUT,
    STATUS_NO_SERVICE,
    STATUS_OK,
)
from ..models import Arrival, EtaResult, RouteInfo, StopInfo, calculate_minutes_away
from .base import BaseProvider

_LOGGER = logging.getLogger(__name__)


class KmbLwbProvider(BaseProvider):
    """Provider for Kowloon Motor Bus and Long Win Bus."""

    operator = OPERATOR_KMB
    name = "KMB / LWB"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__(session)
        self._routes_cache: list[RouteInfo] | None = None
        self._stops_cache: dict[str, StopInfo] = {}

    async def _get_json(self, path: str) -> dict[str, Any] | None:
        url = f"{KMB_API_BASE}{path}"
        try:
            async with self.session.get(
                url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning("KMB API %s returned %s", path, resp.status)
                    return None
                return await resp.json()
        except TimeoutError:
            _LOGGER.warning("KMB API timeout: %s", path)
            raise
        except Exception as err:
            _LOGGER.error("KMB API error %s: %s", path, err)
            return None

    async def get_routes(self) -> list[RouteInfo]:
        """Fetch all KMB/LWB routes."""
        if self._routes_cache is not None:
            return self._routes_cache

        data = await self._get_json("/route/")
        if not data or "data" not in data:
            return []

        routes: list[RouteInfo] = []
        for item in data["data"]:
            # co is not always present in list; both KMB and LWB share this API
            routes.append(
                RouteInfo(
                    operator=OPERATOR_KMB,  # treat LWB under same provider for now
                    route=item.get("route", ""),
                    direction=item.get("bound"),  # "O" or "I"
                    service_type=str(item.get("service_type", "1")),
                    origin=item.get("orig_en"),
                    destination=item.get("dest_en"),
                    bound=item.get("bound"),
                )
            )
        self._routes_cache = routes
        return routes

    async def get_stops_for_route(
        self, route: str, direction: str | None = None, service_type: str | None = None
    ) -> list[StopInfo]:
        """Return ordered stops for a route + direction + service_type.

        direction should be "O"/"I" or "outbound"/"inbound".
        """
        if not direction:
            return []

        # Normalize direction for path
        dir_path = direction.lower()
        if dir_path in ("o", "outbound"):
            dir_path = "outbound"
        elif dir_path in ("i", "inbound"):
            dir_path = "inbound"
        else:
            dir_path = "outbound"

        st = service_type or "1"
        data = await self._get_json(f"/route-stop/{route}/{dir_path}/{st}")
        if not data or "data" not in data:
            return []

        stops: list[StopInfo] = []
        for item in data["data"]:
            stop_id = item.get("stop")
            if not stop_id:
                continue
            # Enrich with stop name if we have it cached
            stop_info = self._stops_cache.get(stop_id)
            if stop_info is None:
                stop_info = StopInfo(stop_id=stop_id, name_en=None, operator=OPERATOR_KMB)
            stops.append(stop_info)
        return stops

    async def search_stops(self, keyword: str) -> list[StopInfo]:
        """Search stops by English name keyword or exact stop_id."""
        keyword_upper = keyword.strip().upper()
        if not keyword_upper:
            return []

        # Ensure we have stop list
        if not self._stops_cache:
            await self._load_all_stops()

        results: list[StopInfo] = []
        for stop in self._stops_cache.values():
            if stop.stop_id.upper() == keyword_upper:
                results.append(stop)
                continue
            if stop.name_en and keyword_upper in stop.name_en.upper():
                results.append(stop)
        return results[:30]  # limit for UI

    async def _load_all_stops(self) -> None:
        """Load full stop list into cache."""
        data = await self._get_json("/stop")
        if not data or "data" not in data:
            return
        for item in data["data"]:
            stop_id = item.get("stop")
            if not stop_id:
                continue
            self._stops_cache[stop_id] = StopInfo(
                stop_id=stop_id,
                name_en=item.get("name_en"),
                name_tc=item.get("name_tc"),
                lat=float(item["lat"]) if item.get("lat") else None,
                long=float(item["long"]) if item.get("long") else None,
                operator=OPERATOR_KMB,
            )

    async def get_stop_name(self, stop_id: str) -> str | None:
        """Return English stop name."""
        if stop_id not in self._stops_cache:
            await self._load_all_stops()
        stop = self._stops_cache.get(stop_id)
        return stop.name_en if stop else None

    async def fetch_eta(
        self,
        stop_id: str,
        route: str,
        direction: str | None = None,
        service_type: str | None = None,
        stop_name: str | None = None,
        destination: str | None = None,
        stop_seq: int | None = None,
    ) -> EtaResult:
        """Fetch ETA for stop + route + service_type."""
        st = service_type or "1"
        now = dt_util.now()

        try:
            data = await self._get_json(f"/eta/{stop_id}/{route}/{st}")
        except TimeoutError:
            return EtaResult(
                operator=OPERATOR_KMB,
                route=route,
                direction=direction,
                service_type=st,
                destination=destination,
                stop_id=stop_id,
                stop_name=stop_name,
                stop_seq=stop_seq,
                status_reason=STATUS_API_TIMEOUT,
                data_source="error",
                last_updated=now,
            )

        if data is None:
            return EtaResult(
                operator=OPERATOR_KMB,
                route=route,
                direction=direction,
                service_type=st,
                destination=destination,
                stop_id=stop_id,
                stop_name=stop_name,
                stop_seq=stop_seq,
                status_reason=STATUS_API_ERROR,
                data_source="error",
                last_updated=now,
            )

        arrivals: list[Arrival] = []
        raw_list = data.get("data") or []

        for item in raw_list:
            # Filter by direction if provided (API may return both bounds)
            item_dir = item.get("dir") or item.get("bound")
            if direction and item_dir and direction.upper() not in (item_dir.upper(),):
                # allow mismatch for now; some responses use different keys
                pass

            eta_str = item.get("eta")
            eta_dt: datetime | None = None
            if eta_str:
                try:
                    eta_dt = dt_util.parse_datetime(eta_str)
                except Exception:
                    eta_dt = None

            minutes = calculate_minutes_away(eta_dt, now)
            rmk = item.get("rmk_en") or item.get("rmk_tc") or ""
            is_scheduled = "scheduled" in rmk.lower() or "原定" in rmk

            arrivals.append(
                Arrival(
                    eta=eta_dt,
                    minutes_away=minutes,
                    destination=item.get("dest_en") or destination,
                    is_scheduled=is_scheduled,
                    remark=rmk or None,
                    eta_seq=item.get("eta_seq"),
                )
            )

        # Sort by eta time
        arrivals.sort(key=lambda a: a.eta or datetime.max.replace(tzinfo=a.eta.tzinfo if a.eta else None))

        status = STATUS_OK if arrivals else STATUS_NO_SERVICE

        return EtaResult(
            operator=OPERATOR_KMB,
            route=route,
            direction=direction,
            service_type=st,
            destination=destination or (arrivals[0].destination if arrivals else None),
            stop_id=stop_id,
            stop_name=stop_name,
            stop_seq=stop_seq,
            upcoming_arrivals=arrivals,
            status_reason=status,
            data_source="live",
            last_updated=now,
        )
