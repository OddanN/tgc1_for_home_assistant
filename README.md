# TGC-1 Integration for Home Assistant

![GitHub Release](https://img.shields.io/github/v/release/OddanN/tgc1_for_home_assistant?style=flat-square)
![GitHub Activity](https://img.shields.io/github/commit-activity/m/OddanN/tgc1_for_home_assistant?style=flat-square)
![GitHub Downloads](https://img.shields.io/github/downloads/OddanN/tgc1_for_home_assistant/total?style=flat-square)
![License](https://img.shields.io/github/license/OddanN/tgc1_for_home_assistant?style=flat-square)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/hacs/integration)

<p align="center">
  <img src="logo.png" alt="TGC-1 logo" width="200">
</p>

The TGC-1 Integration allows you to connect your Home Assistant instance to the TGC-1 personal account at
`https://lk.tgc1.ru/`. The integration performs the same two-step authentication flow as the website, retrieves the
list of linked payment accounts, and exposes diagnostic entities for the configured account set.

## Installation

Installation is easiest via the [Home Assistant Community Store
(HACS)](https://hacs.xyz/), which is the best place to get third-party integrations for Home Assistant. Once you have
HACS set up, simply click the button below (requires My Home Assistant configured) or follow the
[instructions for adding a custom repository](https://hacs.xyz/docs/faq/custom_repositories) and then the integration
will be available to install like any other.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=OddanN&repository=tgc1_for_home_assistant&category=integration)

## Configuration

After installing, configure the integration using the Integrations UI. No manual YAML configuration is required. Go to
Settings / Devices & Services and press the Add Integration button, or click the shortcut button below (requires My
Home Assistant configured).

[![Add Integration to your Home Assistant instance.](https://my.home-assistant.io/badges/config_flow_start.svg?style=flat-square)](https://my.home-assistant.io/redirect/config_flow_start/?domain=tgc1_for_home_assistant)

### Setup Wizard

- **Email**: Enter the email used in your TGC-1 personal account.
- **Password**: Enter your TGC-1 password.
- **Integration settings**: After successful authentication, choose the update interval and select which payment
  accounts should be tracked.

### Authentication Flow

The integration follows the website login sequence:

1. Opens `https://lk.tgc1.ru/` to obtain `session-cookie`.
2. Sends `POST /api/security/auth/login/fl` with your credentials.
3. Stores `accessToken`, `refreshToken`, token type, and `session-cookie` in the config entry.
4. Requests `GET /api/fl/account` to discover available payment accounts.

### Integration Options

- **Update Interval**: Polling interval in hours. Default is 12 hours, minimum is 1 hour, maximum is 24 hours.
- **Accounts**: Choose which payment accounts should be tracked by the integration.

The same settings are also available later from the integration options dialog.

## Usage

### Device Entities

The integration creates one device for the configured TGC-1 account and currently exposes diagnostic entities based on
the available payment account list:

- `sensor.<generated>_accounts_count`: Number of linked payment accounts returned by the API.
- `sensor.<generated>_account_<id>`: A diagnostic sensor for each selected payment account. The sensor state is the
  account number, and the address is exposed in attributes.
- `number.<generated>_scan_interval`: Update interval in hours, editable directly from the device page.
- `button.<generated>_refresh`: Manual refresh button that triggers immediate data reload.

### Current Scope

At the moment, the integration uses `GET /api/fl/account` and exposes the payment account list and integration control
entities. Detailed account balance and billing sensors can be added later when the corresponding API endpoints are
documented.

## Notes

- This integration requires an active TGC-1 personal account.
- Data is fetched from `https://lk.tgc1.ru/`.
- Authentication depends on both bearer tokens and the server-issued `session-cookie`.
- The current version mainly exposes diagnostic entities and integration controls.
- For support or to report issues, open an issue on the
  [GitHub repository](https://github.com/OddanN/tgc1_for_home_assistant/issues).

## Debug

For DEBUG add to `configuration.yaml`

```yaml
logger:
  default: info
  logs:
    custom_components.tgc1_for_home_assistant: debug
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
