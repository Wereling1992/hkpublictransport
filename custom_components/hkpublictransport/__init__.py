"""HK Public Transport custom integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import HkBusEtaCoordinator
from .providers import ProviderHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HK Public Transport from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)

    # Shared hub across all entries (created once)
    if "hub" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["hub"] = ProviderHub(session)

    hub: ProviderHub = hass.data[DOMAIN]["hub"]

    coordinator = HkBusEtaCoordinator(hass, entry, hub)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # Keep the shared hub alive while other entries exist
        if len([k for k in hass.data[DOMAIN] if k != "hub"]) == 0:
            hass.data[DOMAIN].pop("hub", None)
    return unload_ok
