"""Citybus provider – placeholder / partial implementation.

Full implementation will use the official Citybus open data APIs:
https://rt.data.gov.hk/v2/transport/citybus/...
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from ..const import OPERATOR_CTB, STATUS_API_ERROR
from ..models import EtaResult, RouteInfo, StopInfo
from .base import BaseProvider

_LOGGER = logging.getLogger(__name__)


class CitybusProvider(BaseProvider):
    """Citybus provider (stub for now)."""

    operator = OPERATOR_CTB
    name = "Citybus"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__(session)

    async def get_routes(self) -> list[RouteInfo]:
        _LOGGER.debug("Citybus get_routes not fully implemented yet")
        return []

    async def get_stops_for_route(
        self, route: str, direction: str | None = None, service_type: str | None = None
    ) -> list[StopInfo]:
        return []

    async def search_stops(self, keyword: str) -> list[StopInfo]:
        return []

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
        return EtaResult(
            operator=OPERATOR_CTB,
            route=route,
            direction=direction,
            service_type=service_type,
            destination=destination,
            stop_id=stop_id,
            stop_name=stop_name,
            stop_seq=stop_seq,
            status_reason=STATUS_API_ERROR,
            data_source="stub",
        )
