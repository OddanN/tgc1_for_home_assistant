"""Constants for the TGC-1 integration."""

DOMAIN = "tgc1_for_home_assistant"

CONF_ACCOUNTS = "accounts"
CONF_ACCOUNT_IDS = "account_ids"
CONF_ACCOUNT_NAMES = "account_names"
CONF_ACCESS_TOKEN = "access_token"
CONF_LOGIN = "login"
CONF_PASSWORD = "password"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SESSION_COOKIE = "session_cookie"
CONF_TOKEN_TYPE = "token_type"

API_BASE_URL = "https://lk.tgc1.ru"
API_BOOTSTRAP_PATH = "/"
API_ACCOUNTS_PATH = "/api/fl/account"
API_LOGIN_PATH = "/api/security/auth/login/fl"

COOKIE_NAME = "session-cookie"
DEFAULT_TOKEN_TYPE = "Bearer"
DEFAULT_SCAN_INTERVAL_HOURS = 12
