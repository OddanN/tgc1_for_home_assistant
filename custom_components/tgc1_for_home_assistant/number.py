"""Number platform for the TGC-1 integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS, DOMAIN
from .coordinator import Tgc1DataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TGC-1 number entities."""
    coordinator: Tgc1DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([Tgc1ScanIntervalNumber(hass, entry, coordinator)])


class Tgc1ScanIntervalNumber(NumberEntity):
    """Number entity to control scan interval in hours."""

    _attr_name = "Scan Interval"
    _attr_icon = "mdi:timer-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 24
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: Tgc1DataUpdateCoordinator,
    ) -> None:
        """Initialize the number entity."""
        self.hass = hass
        self._entry = entry
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_scan_interval"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="TGC-1",
            model="Personal Cabinet",
            name=entry.title,
        )

    @property
    def native_value(self) -> int:
        """Return current scan interval in hours."""
        return int(
            self._entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS)
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set scan interval in hours."""
        value_int = max(1, min(24, int(round(value))))
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_SCAN_INTERVAL: value_int},
        )
        await self.hass.config_entries.async_reload(self._entry.entry_id)
        self.async_write_ha_state()
