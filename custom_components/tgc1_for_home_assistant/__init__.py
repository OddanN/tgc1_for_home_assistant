"""The TGC-1 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .api import Tgc1ApiClient, Tgc1ClientAuthContext
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_LOGIN,
    CONF_REFRESH_TOKEN,
    CONF_SESSION_COOKIE,
    CONF_TOKEN_TYPE,
    DOMAIN,
)
from .coordinator import Tgc1DataUpdateCoordinator
from .options_flow import Tgc1OptionsFlow

type Tgc1ConfigEntry = ConfigEntry[Tgc1ApiClient]

PLATFORMS = ["sensor", "number", "button"]


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up the integration from YAML."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: Tgc1ConfigEntry) -> bool:
    """Set up TGC-1 from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = Tgc1ApiClient(
        hass,
        Tgc1ClientAuthContext(
            login=entry.data[CONF_LOGIN],
            password=entry.data[CONF_PASSWORD],
            auth_payload={
                key: entry.data[key]
                for key in (CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, CONF_TOKEN_TYPE)
                if key in entry.data
            }
            or None,
            session_cookie=entry.data.get(CONF_SESSION_COOKIE),
        ),
    )

    coordinator = Tgc1DataUpdateCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }
    entry.runtime_data = client
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Tgc1ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates."""
    await hass.config_entries.async_reload(entry.entry_id)


def async_get_options_flow(config_entry: ConfigEntry) -> Tgc1OptionsFlow:
    """Get the options flow for this handler."""
    return Tgc1OptionsFlow(config_entry)
