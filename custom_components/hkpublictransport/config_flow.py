"""Config flow for HK Public Transport."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .providers import ProviderHub

_LOGGER = logging.getLogger(__name__)

STEP_USER_MENU = "user"
STEP_ROUTE = "route"
STEP_ROUTE_SELECT = "route_select"
STEP_STOP_SELECT = "stop_select"
STEP_STOP = "stop"
STEP_STOP_ROUTE_SELECT = "stop_route_select"


class HkBusEtaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HK Public Transport."""

    VERSION = 1

    def __init__(self) -> None:
        self._hub: ProviderHub | None = None
        self._route_options: list[dict[str, Any]] = []
        self._selected_route: dict[str, Any] | None = None
        self._stop_options: list[dict[str, Any]] = []
        self._keyword: str = ""

    async def _get_hub(self) -> ProviderHub:
        if self._hub is None:
            session = async_get_clientsession(self.hass)
            self._hub = ProviderHub(session)
        return self._hub

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show menu: Add by Route or Add by Stop."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["route", "stop"],
        )

    async def async_step_route(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step: enter route number."""
        errors: dict[str, str] = {}

        if user_input is not None:
            route_no = user_input.get("route", "").strip().upper()
            if not route_no:
                errors["base"] = "invalid_route"
            else:
                hub = await self._get_hub()
                self._route_options = await hub.search_routes(route_no)
                if not self._route_options:
                    errors["base"] = "route_not_found"
                else:
                    return await self.async_step_route_select()

        return self.async_show_form(
            step_id="route",
            data_schema=vol.Schema(
                {
                    vol.Required("route"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_route_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select specific operator + direction + service_type."""
        if user_input is not None:
            idx = int(user_input["selection"])
            self._selected_route = self._route_options[idx]
            return await self.async_step_stop_select()

        options = {
            str(i): opt["label"] for i, opt in enumerate(self._route_options)
        }
        return self.async_show_form(
            step_id="route_select",
            data_schema=vol.Schema(
                {
                    vol.Required("selection"): vol.In(options),
                }
            ),
        )

    async def async_step_stop_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a stop along the chosen route."""
        if self._selected_route is None:
            return self.async_abort(reason="no_route")

        hub = await self._get_hub()
        r = self._selected_route

        if user_input is not None:
            idx = int(user_input["stop"])
            # We need to re-fetch stops to get the full list with order
            stops = await hub.get_stops_for_route(
                operator=r["operator"],
                route=r["route"],
                direction=r.get("direction"),
                service_type=r.get("service_type"),
            )
            if idx < 0 or idx >= len(stops):
                return self.async_abort(reason="invalid_stop")

            stop = stops[idx]
            # Try to enrich name
            stop_name = stop.name_en
            if not stop_name and hasattr(hub.providers.get(r["operator"]), "get_stop_name"):
                stop_name = await hub.providers[r["operator"]].get_stop_name(stop.stop_id)

            data = {
                "operator": r["operator"],
                "route": r["route"],
                "direction": r.get("direction"),
                "service_type": r.get("service_type", "1"),
                "destination": r.get("destination"),
                "stop_id": stop.stop_id,
                "stop_name": stop_name or stop.stop_id,
                "stop_seq": idx + 1,
            }

            unique = (
                f"hkpublictransport_{data['operator']}_{data['route']}_"
                f"{data['direction']}_{data['service_type']}_{data['stop_id']}"
            ).lower()
            await self.async_set_unique_id(unique)
            self._abort_if_unique_id_configured()

            title = f"{data['operator'].upper()} {data['route']} - {data['stop_name']}"
            if data.get("destination"):
                title += f" ({data['destination']})"

            return self.async_create_entry(title=title, data=data)

        # Load stops
        stops = await hub.get_stops_for_route(
            operator=r["operator"],
            route=r["route"],
            direction=r.get("direction"),
            service_type=r.get("service_type"),
        )

        if not stops:
            return self.async_abort(reason="no_stops")

        # Enrich names if possible
        provider = hub.get_provider(r["operator"])
        options = {}
        for i, s in enumerate(stops):
            name = s.name_en
            if not name and provider and hasattr(provider, "get_stop_name"):
                name = await provider.get_stop_name(s.stop_id)
            label = f"{i+1}. {name or s.stop_id}"
            options[str(i)] = label

        return self.async_show_form(
            step_id="stop_select",
            data_schema=vol.Schema(
                {
                    vol.Required("stop"): vol.In(options),
                }
            ),
        )

    async def async_step_stop(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add by stop keyword / stop ID."""
        errors: dict[str, str] = {}

        if user_input is not None:
            keyword = user_input.get("keyword", "").strip()
            if not keyword:
                errors["base"] = "invalid_stop"
            else:
                hub = await self._get_hub()
                self._stop_options = await hub.search_stops(keyword)
                if not self._stop_options:
                    errors["base"] = "stop_not_found"
                else:
                    self._keyword = keyword
                    return await self.async_step_stop_route_select()

        return self.async_show_form(
            step_id="stop",
            data_schema=vol.Schema(
                {
                    vol.Required("keyword"): str,
                }
            ),
            errors=errors,
            description_placeholders={"example": "e.g. Tsuen Wan or stop ID"},
        )

    async def async_step_stop_route_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """After choosing a stop, user still needs to pick which route at that stop.
        For MVP we keep it simple: currently only KMB is fully wired,
        so we show the matching stops and let user confirm, then require route input.
        """
        # Simplified for first version: ask for route after stop
        if user_input is not None:
            # For now redirect to route flow with prefilled stop – keep simple
            return await self.async_step_route()

        options = {
            str(i): opt["label"] for i, opt in enumerate(self._stop_options[:20])
        }
        return self.async_show_form(
            step_id="stop_route_select",
            data_schema=vol.Schema(
                {
                    vol.Required("selection"): vol.In(options),
                }
            ),
        )
