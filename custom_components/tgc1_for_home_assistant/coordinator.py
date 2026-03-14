"""Coordinator for the TGC-1 integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Tgc1ApiClient, Tgc1AuthError, Tgc1ConnectionError, Tgc1Error
from .const import CONF_ACCOUNT_IDS, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _coerce_scan_interval(value: Any) -> timedelta:
    """Convert a stored scan interval into a timedelta."""
    hours = DEFAULT_SCAN_INTERVAL_HOURS
    if isinstance(value, (int, float)):
        hours = int(value)
    elif isinstance(value, str):
        try:
            hours = int(float(value))
        except ValueError:
            hours = DEFAULT_SCAN_INTERVAL_HOURS

    hours = max(1, min(24, hours))
    return timedelta(hours=hours)


class Tgc1DataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, str]]]):
    """Coordinate TGC-1 account updates."""

    def __init__(
        self,
        hass,
        client: Tgc1ApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        self.client = client
        self.entry = entry
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=_coerce_scan_interval(
                entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS)
            ),
        )

    async def _async_update_data(self) -> dict[str, dict[str, str]]:
        """Fetch the latest account list."""
        try:
            accounts = await self.client.async_get_accounts()
        except Tgc1AuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except Tgc1ConnectionError as err:
            raise UpdateFailed(str(err)) from err
        except Tgc1Error as err:
            raise UpdateFailed(str(err)) from err

        allowed_account_ids = {
            str(account_id) for account_id in self.entry.options.get(CONF_ACCOUNT_IDS, [])
        }
        data: dict[str, dict[str, str]] = {}
        for account in accounts:
            account_id = account.get("id")
            if account_id is None:
                continue

            account_id_str = str(account_id)
            if allowed_account_ids and account_id_str not in allowed_account_ids:
                continue

            data[account_id_str] = {
                "id": account_id_str,
                "number": str(account.get("number") or account_id_str),
                "address": str(account.get("address") or "").strip(),
            }

        return data
