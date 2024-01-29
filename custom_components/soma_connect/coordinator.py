"""Data update coordinator for SOMA Connect."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import timedelta
import logging

from aiosoma import SomaConnect, SomaShade

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=10)
DELAY_BEFORE_UPDATE = 1.0

_LOGGER = logging.getLogger(__name__)


class SomaConnectUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for SOMA Connect."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialise the SOMA Connect data update coordinator."""
        self._hass = hass
        self._soma = SomaConnect(host, port)
        self._soma_version: str = ""
        self._shades: dict[str, SomaShade] = {}
        self._availability: dict[str, bool] = {}
        self._get_light_levels: dict[str, bool] = {}
        self._light_levels: dict[str, int] = {}
        self._positions: dict[str, int] = {}
        self._battery_levels: dict[str, int] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=DELAY_BEFORE_UPDATE, immediate=False
            ),
        )

    @property
    def soma_connect(self) -> SomaConnect:
        """Return the SomaConnect object."""
        return self._soma

    @property
    def soma_version(self) -> str:
        """Return the SOMA Connection version."""
        return self._soma_version

    @property
    def shades(self) -> list[SomaShade]:
        """Return a list of shades."""
        return list(self._shades.values())

    def is_shade_available(self, mac: str) -> bool:
        """Return availability of specified shade."""
        return bool(self._availability.get(mac))

    def get_position(self, mac: str) -> int | None:
        """Return the position of the specified shade."""
        return self._positions[mac]

    def get_battery_level(self, mac: str) -> int | None:
        """Return the battery level of the specified shade."""
        return self._battery_levels[mac]

    def get_light_level(self, mac: str) -> int | None:
        """Return the light level of the specified shade."""
        return self._light_levels[mac]

    async def _async_update_data(self) -> None:
        """Fetch data for all shades."""
        device_list = await self.soma_connect.list_devices()
        self._soma_version = self.soma_connect.version

        for device in device_list:
            shade = SomaShade(
                self.soma_connect,
                name=device[0],
                mac=device[1],
                type=device[2],
                gen=device[3],
            )

            self._shades[shade.mac] = shade
            self._availability[shade.mac] = True

            _LOGGER.debug(
                "Will update position and battery level for shade: %s (%s)",
                shade.name,
                shade.mac,
            )

            # Update position and battery level every cycle
            tasks = [shade.get_current_position(), shade.get_current_battery_level()]

            # Update light level if sensor is enabled.
            if self._get_light_levels.get(shade.mac, False) is True:
                _LOGGER.debug(
                    "Adding light level to request for shade: %s (%s)",
                    shade.name,
                    shade.mac,
                )
                tasks.append(shade.get_current_light_level())

            responses = await asyncio.gather(*tasks)

            # Set shade unavailable if no value for position or battery level
            if responses[0] is None or responses[1] is None:
                _LOGGER.debug(
                    "No data returned from SOMA Connect for shade: %s (%s)",
                    shade.name,
                    shade.mac,
                )
                self._availability[shade.mac] = False

            # Save the position and battery level values
            if len(responses) >= 2:
                self._positions[shade.mac] = int(100 - shade.position)
                self._battery_levels[shade.mac] = int(shade.battery_percentage)
                _LOGGER.debug(
                    "SOMA Connect reported shade %s (%s) position: %s",
                    shade.name,
                    shade.mac,
                    self._positions[shade.mac],
                )
                _LOGGER.debug(
                    "SOMA Connect reported shade %s (%s) battery level: %s",
                    shade.name,
                    shade.mac,
                    self._battery_levels[shade.mac],
                )

            # Save light level if it was retrieved
            if len(responses) == 3:
                light_level = int(shade.light_level)
                self._light_levels[shade.mac] = light_level
                _LOGGER.debug(
                    "SOMA Connect reported shade %s (%s) light level: %s",
                    shade.name,
                    shade.mac,
                    self._light_levels[shade.mac],
                )

        # If any device failed to return a position or battery level value
        # set the update as failed
        if False in self._availability.values():
            raise UpdateFailed()

    async def open_shade(self, mac: str) -> None:
        """Open the specified shade."""
        await self.soma_connect.open_shade(mac)

    async def close_shade(self, mac: str) -> None:
        """Close the specified shade."""
        await self.soma_connect.close_shade(mac)

    async def stop_shade(self, mac: str) -> None:
        """Stop the specified shade."""
        await self.soma_connect.stop_shade(mac)

    async def set_shade_position(self, mac: str, position: int, **kwargs) -> None:
        """Set the shade to the specified position."""
        close_upwards = kwargs.pop("close_upwards", False)
        morning_mode = kwargs.pop("morning_mode", False)
        await self.soma_connect.set_shade_position(
            mac, position, close_upwards=close_upwards, morning_mode=morning_mode
        )

    async def async_enable_light_level_updates(self, mac: str) -> Callable[[], None]:
        """Enable light level updates and update the light level."""

        @callback
        def _async_disable_light_level_updates() -> None:
            """Disable light level updates when sensor removed."""
            self._get_light_levels[mac] = False

        self._light_levels[mac] = await self.soma_connect.get_light_level(mac)
        self._get_light_levels[mac] = True

        return _async_disable_light_level_updates
