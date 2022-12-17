"""Support for Soma Covers."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from aiosoma import Shade

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SOMA, DEVICES, DOMAIN, SomaConnectEntity

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soma cover platform."""

    soma = hass.data[DOMAIN][SOMA]
    shades: list[Shade] = [Shade(soma, **shade) for shade in hass.data[DOMAIN][DEVICES]]
    entities: list[SomaConnectTilt | SomaConnectShade] = []

    for shade in shades:
        # Assume a shade device if the type is not present in the api response (Connect <2.2.6)
        if shade.model == "tilt":
            entities.append(SomaConnectTilt(shade, soma))
        else:
            entities.append(SomaConnectShade(shade, soma))

    async_add_entities(entities, True)


class SomaConnectTilt(SomaConnectEntity, CoverEntity):
    """Representation of a Soma Tilt device."""

    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.STOP_TILT
        | CoverEntityFeature.SET_TILT_POSITION
    )

    @property
    def current_cover_tilt_position(self) -> int:
        """Return the current cover tilt position."""
        return int(self.current_position)

    @property
    def is_closed(self) -> bool:
        """Return if the cover tilt is closed."""
        return self.current_position == 0

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        await self.shade.set_position(100)

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        await self.shade.set_position(-100)
        self.set_position(100)

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the cover tilt."""
        await self.shade.stop()
        # Set cover position to some value where up/down are both enabled
        self.set_position(50)

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        # 0 -> Closed down (api: 100)
        # 50 -> Fully open (api: 0)
        # 100 -> Closed up (api: -100)
        target_position = 100 - ((int(kwargs.pop(ATTR_TILT_POSITION)) / 50) * 100)
        if 50 <= target_position <= 100:
            kwargs["close_upwards"] = True
        await self.shade.set_position(target_position, **kwargs)

        self.set_position(kwargs[ATTR_TILT_POSITION])

    async def async_update(self) -> None:
        """Update the entity with the latest data."""
        response = await self.shade.get_state()
        shade_position = int(response["position"])

        if "closed_upwards" in response.keys():
            self.current_position = 50 + ((shade_position * 50) / 100)
        else:
            self.current_position = 50 - ((shade_position * 50) / 100)


class SomaConnectShade(SomaConnectEntity, CoverEntity):
    """Representation of a SOMA Connect Shade device."""

    _attr_device_class = CoverDeviceClass.SHADE
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    @property
    def current_cover_position(self) -> int:
        """Return the current cover position."""
        return int(self.current_position)

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        return self.current_position == 0

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        _LOGGER.debug("Closing %s (%s)", self.shade.name, self.shade.mac)
        await self.shade.close(**kwargs)

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        _LOGGER.debug("Opening %s (%s)", self.shade.name, self.shade.mac)
        await self.shade.open(**kwargs)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        _LOGGER.debug("Stopping %s (%s)", self.shade.name, self.shade.mac)
        await self.shade.stop()

        # Set cover position to some value where up/down are both enabled
        self.set_position(50)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover shutter to a specific position."""
        self.current_position = int(kwargs.pop(ATTR_POSITION))
        _LOGGER.debug(
            "Soft positioning %s (%s) to position %i",
            self.shade.name,
            self.shade.mac,
            100 - self.current_position,
        )
        await self.shade.set_position(100 - self.current_position)

    async def async_update(self) -> None:
        """Update the cover with the latest data."""

        response = await self.shade.get_state()
        position = int(response.get("position", None))

        _LOGGER.debug(
            "Actual shade position: %i for %s (%s)",
            position,
            self.shade.name,
            self.shade.mac,
        )
        if position is not None:
            self.current_position = 100 - position
