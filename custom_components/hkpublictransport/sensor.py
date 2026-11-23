"""Sensor platform for HK Public Transport."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HkBusEtaCoordinator
from .models import EtaResult


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor from a config entry."""
    coordinator: HkBusEtaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HkBusEtaSensor(coordinator, entry)])


class HkBusEtaSensor(CoordinatorEntity[HkBusEtaCoordinator], SensorEntity):
    """Representation of a HK Public Transport ETA sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:bus-clock"
    _attr_has_entity_name = True

    def __init__(self, coordinator: HkBusEtaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        cfg = entry.data

        operator = cfg.get("operator", "kmb").upper()
        route = cfg["route"]
        stop_name = cfg.get("stop_name") or cfg.get("stop_id", "")
        dest = cfg.get("destination") or ""

        self._attr_unique_id = (
            f"hkpublictransport_{cfg.get('operator', 'kmb')}_{route}_"
            f"{cfg.get('direction', '')}_{cfg.get('service_type', '1')}_{cfg['stop_id']}"
        ).lower()

        self._attr_name = f"{operator} {route} - {stop_name}"
        if dest:
            self._attr_name += f" ({dest})"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"HK Bus {operator} {route}",
            "manufacturer": "HK Public Transport",
            "model": operator,
        }

    @property
    def native_value(self) -> int | None:
        """Return minutes until next bus."""
        data: EtaResult | None = self.coordinator.data
        if data is None:
            return None
        return data.state_minutes

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        data: EtaResult | None = self.coordinator.data
        if data is None:
            return {}
        return data.to_attributes()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
