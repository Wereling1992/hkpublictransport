"""Provider aggregator for HK Public Transport."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from ..const import OPERATOR_CTB, OPERATOR_KMB, OPERATOR_NLB
from ..models import EtaResult, RouteInfo, StopInfo
from .base import BaseProvider
from .kmb_lwb import KmbLwbProvider

_LOGGER = logging.getLogger(__name__)

# Citybus and NLB will be added later; keep placeholders for structure
try:
    from .citybus import CitybusProvider
except ImportError:
    CitybusProvider = None  # type: ignore

try:
    from .nlb import NlbProvider
except ImportError:
    NlbProvider = None  # type: ignore


class ProviderHub:
    """Aggregates multiple operator providers and provides unified search."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session
        self.providers: dict[str, BaseProvider] = {
            OPERATOR_KMB: KmbLwbProvider(session),
        }
        if CitybusProvider is not None:
            self.providers[OPERATOR_CTB] = CitybusProvider(session)
        if NlbProvider is not None:
            self.providers[OPERATOR_NLB] = NlbProvider(session)

    def get_provider(self, operator: str) -> BaseProvider | None:
        return self.providers.get(operator.lower())

    async def search_routes(self, route_number: str) -> list[dict[str, Any]]:
        """Search routes across all providers. Returns list of option dicts for Config Flow."""
        route_number = route_number.strip().upper()
        results: list[dict[str, Any]] = []

        for op, provider in self.providers.items():
            try:
                routes = await provider.get_routes()
                for r in routes:
                    if r.route.upper() == route_number:
                        results.append(
                            {
                                "operator": r.operator,
                                "route": r.route,
                                "direction": r.direction,
                                "service_type": r.service_type,
                                "origin": r.origin,
                                "destination": r.destination,
                                "label": f"{r.operator.upper()} {r.route} → {r.destination or '?'} ({r.direction})",
                            }
                        )
            except Exception as err:
                _LOGGER.warning("Route search failed for %s: %s", op, err)

        return results

    async def search_stops(self, keyword: str) -> list[dict[str, Any]]:
        """Search stops across providers."""
        results: list[dict[str, Any]] = []
        for op, provider in self.providers.items():
            try:
                stops = await provider.search_stops(keyword)
                for s in stops:
                    results.append(
                        {
                            "operator": s.operator or op,
                            "stop_id": s.stop_id,
                            "name_en": s.name_en,
                            "label": f"{s.name_en or s.stop_id} ({s.stop_id})",
                        }
                    )
            except Exception as err:
                _LOGGER.warning("Stop search failed for %s: %s", op, err)
        return results

    async def get_stops_for_route(
        self, operator: str, route: str, direction: str | None, service_type: str | None
    ) -> list[StopInfo]:
        provider = self.get_provider(operator)
        if not provider:
            return []
        return await provider.get_stops_for_route(route, direction, service_type)

    async def fetch_eta(
        self,
        operator: str,
        stop_id: str,
        route: str,
        direction: str | None = None,
        service_type: str | None = None,
        stop_name: str | None = None,
        destination: str | None = None,
        stop_seq: int | None = None,
    ) -> EtaResult:
        provider = self.get_provider(operator)
        if not provider:
            return EtaResult(
                operator=operator,
                route=route,
                direction=direction,
                service_type=service_type,
                destination=destination,
                stop_id=stop_id,
                stop_name=stop_name,
                stop_seq=stop_seq,
                status_reason="api_error",
                data_source="error",
            )
        return await provider.fetch_eta(
            stop_id=stop_id,
            route=route,
            direction=direction,
            service_type=service_type,
            stop_name=stop_name,
            destination=destination,
            stop_seq=stop_seq,
        )
