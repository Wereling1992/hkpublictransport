"""Abstract base provider for bus operators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import aiohttp

from ..models import EtaResult, RouteInfo, StopInfo


class BaseProvider(ABC):
    """Base class for operator-specific providers."""

    operator: str
    name: str

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session

    @abstractmethod
    async def get_routes(self) -> list[RouteInfo]:
        """Return list of routes for this operator."""

    @abstractmethod
    async def get_stops_for_route(
        self, route: str, direction: str | None = None, service_type: str | None = None
    ) -> list[StopInfo]:
        """Return ordered stops for a route."""

    @abstractmethod
    async def search_stops(self, keyword: str) -> list[StopInfo]:
        """Search stops by name or stop_id keyword."""

    @abstractmethod
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
        """Fetch real-time ETA for a specific stop + route."""

    async def close(self) -> None:
        """Optional cleanup."""
        pass
