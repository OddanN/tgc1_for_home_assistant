"""Button platform for the TGC-1 integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import Tgc1DataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TGC-1 button entities."""
    coordinator: Tgc1DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([Tgc1RefreshButton(entry, coordinator)])


class Tgc1RefreshButton(CoordinatorEntity[Tgc1DataUpdateCoordinator], ButtonEntity):
    """Button to force update account data."""

    _attr_name = "Refresh"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: Tgc1DataUpdateCoordinator,
    ) -> None:
        """Initialize the button."""
        CoordinatorEntity.__init__(self, coordinator)
        ButtonEntity.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="TGC-1",
            model="Personal Cabinet",
            name=entry.title,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_refresh()
