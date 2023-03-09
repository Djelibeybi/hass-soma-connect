"""Cover entity for SOMA Connect."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiosoma import SomaShade

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SomaConnectUpdateCoordinator
from .entity import SomaConnectEntity

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soma cover platform."""

    coordinator: SomaConnectUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [SomaConnectShade(coordinator, shade) for shade in coordinator.shades], True
    )


class SomaConnectShade(SomaConnectEntity, CoverEntity):
    """Representation of a SOMA Connect Shade device."""

    def __init__(
        self, coordinator: SomaConnectUpdateCoordinator, shade: SomaShade
    ) -> None:
        super().__init__(coordinator, shade)
        self._attr_name = "Shade"
        self._attr_unique_id = self._shade.mac
        self._attr_device_class = CoverDeviceClass.SHADE
        self._attr_has_entity_name = True
        self._attr_current_cover_position = shade.position
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        return bool(self.current_cover_position == 0)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        _LOGGER.debug("Closing %s", self.name)
        await self.coordinator.close_shade(self._shade.mac)
        self.async_schedule_update_ha_state(True)

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        _LOGGER.debug("Opening %s", self.name)
        await self.coordinator.open_shade(self._shade.mac)
        self.async_schedule_update_ha_state(True)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        _LOGGER.debug("Stopping %s", self.name)
        await self.coordinator.stop_shade(self._shade.mac)
        self.async_schedule_update_ha_state(True)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover shutter to a specific position."""
        set_position = int(100 - kwargs.pop(ATTR_POSITION))
        _LOGGER.debug("Setting %s to %s", self.name, set_position)
        await self.coordinator.set_shade_position(self._shade.mac, set_position)
        self.async_schedule_update_ha_state(True)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    def _async_update_attrs(self) -> None:
        """Update position attribute."""
        self._attr_current_cover_position = self.coordinator.get_position(
            self._shade.mac
        )
