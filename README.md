# SOMA Connect for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]

This custom component is intended to be used instead of the core `soma` integration.
It uses more resilient methods of communicating with the SOMA Connect device and
provides additional entities including battery and light levels.

## Platforms

This integration creates entities in the following platforms:

Platform | Description
-- | --
`cover` | A `cover` entity is created for each Shade device discovered.
`sensor` | Two `sensor` entities are created for each device: one for the battery level and the other for the light level.

The cover entity supports Open, Close, Stop and Set Position.

### Limitations

This integration does not (yet) support Tilt devices as I don't have one to test
with. If I get one, I'll add support for it.

## Installation

1. Add <https://github.com/Djelibeybi/hass-soma-connect> to HACS as a [custom repository][hacs_custom].
1. Click install.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "SOMA Connect (Custom)".

## Configuration

Provide the hostname (or IP address) and port (usually 3000) for your SOMA Connect
appliance when prompted. Home Assistant should then display all the blinds seen
by the appliance.

You can select an area for each shade during the onboarding process or after the
shade entities have been created.

***

[soma_connect]: https://github.com/Djelibeybi/soma-connect
[commits-shield]: https://img.shields.io/github/commit-activity/y/Djelibeybi/hass-soma-connect.svg?style=for-the-badge
[commits]: https://github.com/Djelibeybi/hass-soma-connect/commits/main
[hacs]: https://hacs.xyz
[hacs_custom]: https://hacs.xyz/docs/faq/custom_repositories
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license]: https://github.com/Djelibeybi/hass-soma-connect/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/Djelibeybi/hass-soma-connect.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/Djelibeybi/hass-soma-connect.svg?style=for-the-badge
[releases]: https://github.com/Djelibeybi/hass-soma-connect/releases
