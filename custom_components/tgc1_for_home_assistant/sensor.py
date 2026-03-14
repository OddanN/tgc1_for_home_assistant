"""Sensor platform for the TGC-1 integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LOGIN, DOMAIN
from .coordinator import Tgc1DataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TGC-1 sensors from a config entry."""
    coordinator: Tgc1DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = [Tgc1AccountCountSensor(entry, coordinator)]
    entities.extend(
        Tgc1AccountInfoSensor(entry, coordinator, account_id)
        for account_id in coordinator.data.keys()
    )
    async_add_entities(entities)


class Tgc1BaseCoordinatorSensor(CoordinatorEntity[Tgc1DataUpdateCoordinator], SensorEntity):
    """Base coordinator-backed sensor for TGC-1."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: Tgc1DataUpdateCoordinator,
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="TGC-1",
            model="Personal Cabinet",
            name=entry.title,
        )


class Tgc1AccountCountSensor(Tgc1BaseCoordinatorSensor):
    """Sensor that shows the number of linked payment accounts."""

    _attr_name = "Accounts"
    _attr_icon = "mdi:counter"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: Tgc1DataUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_accounts_count"

    @property
    def native_value(self) -> int:
        """Return the current number of linked accounts."""
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {
            "login": self._entry.data.get(CONF_LOGIN),
            "account_ids": list(self.coordinator.data.keys()),
            "account_numbers": [
                payload["number"] for payload in self.coordinator.data.values()
            ],
        }


class Tgc1AccountInfoSensor(Tgc1BaseCoordinatorSensor):
    """Sensor that exposes a payment account number and metadata."""

    _attr_icon = "mdi:home-city-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: Tgc1DataUpdateCoordinator,
        account_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(entry, coordinator)
        self._account_id = account_id
        account = coordinator.data[account_id]
        self._attr_name = f"Account {account['number']}"
        self._attr_unique_id = f"{entry.entry_id}_account_{account_id}"

    @property
    def native_value(self) -> str | None:
        """Return the account number."""
        account = self.coordinator.data.get(self._account_id)
        if not account:
            return None
        return account["number"]

    @property
    def available(self) -> bool:
        """Return availability based on coordinator data."""
        return self._account_id in self.coordinator.data

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        account = self.coordinator.data.get(self._account_id, {})
        return {
            "account_id": self._account_id,
            "address": account.get("address"),
        }
