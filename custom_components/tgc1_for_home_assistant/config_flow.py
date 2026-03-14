"""Config flow for the TGC-1 integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
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

from .api import Tgc1ApiClient, Tgc1AuthError, Tgc1ClientAuthContext, Tgc1ConnectionError, Tgc1Error
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
    DOMAIN,
)
from .options_flow import Tgc1OptionsFlow


def _normalize_login(login: str) -> str:
    """Normalize login value for storage and unique IDs."""
    return login.strip().lower()


# noinspection PyTypeChecker
class Tgc1ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TGC-1."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._login: str | None = None
        self._password: str | None = None
        self._reauth_entry: ConfigEntry | None = None
        self._auth_payload: dict[str, Any] | None = None
        self._session_cookie: str | None = None
        self._account_map: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._login = _normalize_login(user_input[CONF_LOGIN])
            self._password = user_input[CONF_PASSWORD]

            if self._reauth_entry is None:
                await self.async_set_unique_id(self._login)
                self._abort_if_unique_id_configured()

            client = self._build_client()
            try:
                self._auth_payload = await client.async_authenticate()
                self._session_cookie = client.session_cookie
                accounts = await client.async_get_accounts()
            except Tgc1AuthError:
                errors["base"] = "invalid_auth"
            except Tgc1ConnectionError:
                errors["base"] = "cannot_connect"
            except Tgc1Error:
                errors["base"] = "unknown"
            else:
                self._account_map = _build_account_name_map(accounts)
                return await self.async_step_settings()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOGIN, default=self._login or ""): str,
                    vol.Required(CONF_PASSWORD, default=self._password or ""): str,
                }
            ),
            errors=errors,
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure scan interval and tracked accounts after auth."""
        if not self._auth_payload or self._login is None or self._password is None:
            return self.async_abort(reason="unknown")

        if user_input is not None:
            selected_accounts = [
                account_id
                for account_id in user_input[CONF_ACCOUNT_IDS]
                if account_id in self._account_map
            ]
            data = {
                CONF_LOGIN: self._login,
                CONF_PASSWORD: self._password,
                CONF_ACCESS_TOKEN: self._auth_payload.get(CONF_ACCESS_TOKEN),
                CONF_REFRESH_TOKEN: self._auth_payload.get(CONF_REFRESH_TOKEN),
                CONF_SESSION_COOKIE: self._session_cookie,
                CONF_TOKEN_TYPE: self._auth_payload.get(CONF_TOKEN_TYPE),
                CONF_ACCOUNT_NAMES: self._account_map,
            }
            options = {
                CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                CONF_ACCOUNT_IDS: selected_accounts,
            }

            if self._reauth_entry is not None:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    title=self._login,
                    data={**self._reauth_entry.data, **data},
                    options={**self._reauth_entry.options, **options},
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

            return self.async_create_entry(
                title=self._login,
                data=data,
                options=options,
            )

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=(
                            self._reauth_entry.options.get(
                                CONF_SCAN_INTERVAL,
                                DEFAULT_SCAN_INTERVAL_HOURS,
                            )
                            if self._reauth_entry is not None
                            else DEFAULT_SCAN_INTERVAL_HOURS
                        ),
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
                        default=(
                            [
                                account_id
                                for account_id in self._reauth_entry.options.get(
                                    CONF_ACCOUNT_IDS,
                                    list(self._account_map.keys()),
                                )
                                if account_id in self._account_map
                            ]
                            if self._reauth_entry is not None
                            else list(self._account_map.keys())
                        ),
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

    async def async_step_reauth(self, _entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauthentication triggered by Home Assistant."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if self._reauth_entry is None:
            return self.async_abort(reason="unknown")

        self._login = self._reauth_entry.data[CONF_LOGIN]
        self._password = self._reauth_entry.data[CONF_PASSWORD]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for password during reauthentication."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._password = user_input[CONF_PASSWORD]
            return await self.async_step_user(
                {
                    CONF_LOGIN: self._login or "",
                    CONF_PASSWORD: self._password,
                }
            )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"login": self._login or ""},
            errors=errors,
        )

    def _build_client(self) -> Tgc1ApiClient:
        """Build an API client from current flow state."""
        auth_payload = None
        session_cookie = None
        if self._reauth_entry is not None:
            auth_payload = {
                key: self._reauth_entry.data.get(key)
                for key in (CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, CONF_TOKEN_TYPE)
                if self._reauth_entry.data.get(key) is not None
            }
            session_cookie = self._reauth_entry.data.get(CONF_SESSION_COOKIE)

        return Tgc1ApiClient(
            self.hass,
            Tgc1ClientAuthContext(
                login=self._login or "",
                password=self._password or "",
                auth_payload=auth_payload or None,
                session_cookie=session_cookie,
            ),
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> Tgc1OptionsFlow:
        """Get the options flow for this handler."""
        return Tgc1OptionsFlow(config_entry)


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
