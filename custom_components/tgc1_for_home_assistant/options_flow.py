"""Options flow for the TGC-1 integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import (
    Tgc1ApiClient,
    Tgc1AuthError,
    Tgc1ClientAuthContext,
    Tgc1ConnectionError,
    Tgc1Error,
)
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_ACCOUNT_IDS,
    CONF_ACCOUNT_NAMES,
    CONF_LOGIN,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_SESSION_COOKIE,
    CONF_TOKEN_TYPE,
    DEFAULT_SCAN_INTERVAL_HOURS,
)


class Tgc1OptionsFlow(OptionsFlow):
    """Handle options for TGC-1."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry
        self._account_map: dict[str, str] = dict(config_entry.data.get(CONF_ACCOUNT_NAMES, {}))
        self._selected_accounts: list[str] = list(
            config_entry.options.get(
                CONF_ACCOUNT_IDS,
                config_entry.data.get(CONF_ACCOUNT_IDS, []),
            )
        )
        self._scan_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL_HOURS,
        )

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage integration options."""
        if not self._account_map:
            await self._async_load_accounts()

        if user_input is not None:
            selected_accounts = [
                account_id
                for account_id in user_input[CONF_ACCOUNT_IDS]
                if account_id in self._account_map
            ]
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    CONF_ACCOUNT_IDS: selected_accounts,
                },
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self._scan_interval,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=24,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="h",
                        )
                    ),
                    vol.Required(
                        CONF_ACCOUNT_IDS,
                        default=[
                            account_id
                            for account_id in self._selected_accounts
                            if account_id in self._account_map
                        ],
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=account_id, label=label)
                                for account_id, label in self._account_map.items()
                            ],
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def _async_load_accounts(self) -> None:
        """Load accounts from API when entry data is incomplete."""
        client = Tgc1ApiClient(
            self.hass,
            Tgc1ClientAuthContext(
                login=self._config_entry.data[CONF_LOGIN],
                password=self._config_entry.data[CONF_PASSWORD],
                auth_payload={
                    key: self._config_entry.data[key]
                    for key in (CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, CONF_TOKEN_TYPE)
                    if key in self._config_entry.data
                }
                or None,
                session_cookie=self._config_entry.data.get(CONF_SESSION_COOKIE),
            ),
        )
        try:
            accounts = await client.async_get_accounts()
        except (Tgc1AuthError, Tgc1ConnectionError, Tgc1Error):
            accounts = []

        self._account_map = _build_account_name_map(accounts)


def _build_account_name_map(accounts: list[dict[str, Any]]) -> dict[str, str]:
    """Build readable account labels from the API payload."""
    account_map: dict[str, str] = {}
    for account in accounts:
        account_id = account.get("id")
        if account_id is None:
            continue

        number = str(account.get("number") or account_id)
        address = str(account.get("address") or "").strip()
        label = number if not address else f"{number}: {address}"
        account_map[str(account_id)] = label

    return account_map
