"""New Lantao Bus (NLB) provider – placeholder.

Uses https://rt.data.gov.hk/v2/transport/nlb/ endpoints.
"""

from __future__ import annotations

import logging

import aiohttp

from ..const import OPERATOR_NLB, STATUS_API_ERROR
from ..models import EtaResult, RouteInfo, StopInfo
from .base import BaseProvider

_LOGGER = logging.getLogger(__name__)


class NlbProvider(BaseProvider):
    """NLB provider (stub for now)."""

    operator = OPERATOR_NLB
    name = "NLB"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__(session)

    async def get_routes(self) -> list[RouteInfo]:
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
            operator=OPERATOR_NLB,
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
