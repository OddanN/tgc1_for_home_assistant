"""API client for TGC-1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_ACCOUNTS_PATH,
    API_BASE_URL,
    API_BOOTSTRAP_PATH,
    API_LOGIN_PATH,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_TYPE,
    COOKIE_NAME,
    DEFAULT_TOKEN_TYPE,
)


class Tgc1Error(Exception):
    """Base exception for the integration."""


class Tgc1AuthError(Tgc1Error):
    """Raised when authentication fails."""


class Tgc1ConnectionError(Tgc1Error):
    """Raised when the API is unavailable."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class Tgc1ClientAuthContext:
    """Authentication inputs and persisted tokens for the API client."""

    login: str
    password: str
    auth_payload: dict[str, Any] | None = None
    session_cookie: str | None = None


class Tgc1ApiClient:
    """Thin API client for TGC-1."""

    def __init__(self, hass: HomeAssistant, auth_context: Tgc1ClientAuthContext) -> None:
        """Initialize the client."""
        self._session = async_get_clientsession(hass)
        self._login = auth_context.login
        self._password = auth_context.password
        self._auth_payload = auth_context.auth_payload
        self._session_cookie = auth_context.session_cookie

    @property
    def auth_payload(self) -> dict[str, Any] | None:
        """Return the last successful auth payload."""
        return self._auth_payload

    @property
    def access_token(self) -> str | None:
        """Return the stored access token."""
        if not self._auth_payload:
            return None
        return self._auth_payload.get(CONF_ACCESS_TOKEN)

    @property
    def token_type(self) -> str:
        """Return the stored token type."""
        if not self._auth_payload:
            return DEFAULT_TOKEN_TYPE
        return self._auth_payload.get(CONF_TOKEN_TYPE, DEFAULT_TOKEN_TYPE)

    @property
    def session_cookie(self) -> str | None:
        """Return the stored session cookie."""
        return self._session_cookie

    async def async_authenticate(self) -> dict[str, Any]:
        """Authenticate against the TGC-1 API."""
        await self._async_initialize_session()

        url = f"{API_BASE_URL}{API_LOGIN_PATH}"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": API_BASE_URL,
            "Referer": f"{API_BASE_URL}/fl/login",
        }
        payload = {
            "username": self._login,
            "password": self._password,
        }

        try:
            async with self._session.post(
                url,
                headers=headers,
                json=payload,
                cookies=self._cookie_jar(),
            ) as response:
                self._update_session_cookie(response)
                if response.status in (400, 401, 403):
                    raise Tgc1AuthError("Invalid credentials")

                if response.status >= 500:
                    raise Tgc1ConnectionError(
                        f"TGC-1 API is temporarily unavailable: HTTP {response.status}",
                        status_code=response.status,
                    )

                if response.status >= 400:
                    text = await response.text()
                    raise Tgc1Error(f"Unexpected API response: {response.status} {text}")

                data = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise Tgc1ConnectionError("Unable to connect to TGC-1") from err

        if not data.get("accessToken"):
            raise Tgc1AuthError("Authentication succeeded without access token")

        self._auth_payload = {
            CONF_ACCESS_TOKEN: data.get("accessToken"),
            CONF_REFRESH_TOKEN: data.get("refreshToken"),
            CONF_TOKEN_TYPE: data.get("type", DEFAULT_TOKEN_TYPE),
        }
        return self._auth_payload

    async def async_get_accounts(self) -> list[dict[str, Any]]:
        """Fetch the list of payment accounts."""
        data = await self.async_request(
            "GET",
            API_ACCOUNTS_PATH,
        )
        if not isinstance(data, list):
            raise Tgc1Error("Unexpected accounts payload")
        return data

    async def async_request(
        self,
        method: str,
        path: str,
        *,
        json_payload: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        """Perform an authenticated request."""
        if not self.access_token:
            await self.async_authenticate()

        url = f"{API_BASE_URL}{path}"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"{self.token_type} {self.access_token}",
        }

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                json=json_payload,
                cookies=self._cookie_jar(),
            ) as response:
                self._update_session_cookie(response)
                if response.status in (401, 403):
                    if not retry_auth:
                        raise Tgc1AuthError("Stored token is no longer valid")
                    await self.async_authenticate()
                    return await self.async_request(
                        method,
                        path,
                        json_payload=json_payload,
                        retry_auth=False,
                    )

                if response.status >= 500:
                    raise Tgc1ConnectionError(
                        f"TGC-1 API is temporarily unavailable: HTTP {response.status}",
                        status_code=response.status,
                    )

                if response.status >= 400:
                    text = await response.text()
                    raise Tgc1Error(f"Unexpected API response: {response.status} {text}")

                if response.content_type == "application/json":
                    return await response.json(content_type=None)

                text = await response.text()
                return text
        except (aiohttp.ClientError, TimeoutError) as err:
            raise Tgc1ConnectionError("Unable to connect to TGC-1") from err

    async def _async_initialize_session(self) -> None:
        """Load the landing page to obtain the session cookie."""
        if self._session_cookie:
            return

        url = f"{API_BASE_URL}{API_BOOTSTRAP_PATH}"
        headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

        try:
            async with self._session.get(url, headers=headers) as response:
                self._update_session_cookie(response)
                if response.status >= 500:
                    raise Tgc1ConnectionError(
                        f"TGC-1 website is temporarily unavailable: HTTP {response.status}",
                        status_code=response.status,
                    )
                if response.status >= 400:
                    text = await response.text()
                    raise Tgc1Error(
                        f"Unable to initialize TGC-1 session: {response.status} {text}"
                    )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise Tgc1ConnectionError("Unable to connect to TGC-1") from err

        if not self._session_cookie:
            raise Tgc1AuthError("TGC-1 did not return the expected session cookie")

    def _cookie_jar(self) -> dict[str, str]:
        """Build a cookie dict for aiohttp requests."""
        if not self._session_cookie:
            return {}
        return {COOKIE_NAME: self._session_cookie}

    def _update_session_cookie(self, response: aiohttp.ClientResponse) -> None:
        """Persist the session cookie from a response."""
        cookie = response.cookies.get(COOKIE_NAME)
        if cookie and cookie.value:
            self._session_cookie = cookie.value
