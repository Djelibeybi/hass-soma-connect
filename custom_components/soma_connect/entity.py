"""Base entity for SOMA Connect."""
from __future__ import annotations

from aiosoma import SomaShade

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SomaConnectUpdateCoordinator


class SomaConnectEntity(CoordinatorEntity[SomaConnectUpdateCoordinator]):
    """Representation of SOMA Connect shade."""

    def __init__(
        self, coordinator: SomaConnectUpdateCoordinator, shade: SomaShade
    ) -> None:
        """Initialize an individual SOMA shade."""

        super().__init__(coordinator)
        self._shade: SomaShade = shade

    @property
    def available(self) -> bool:
        """Return true if the last API commands returned successfully."""
        return self.coordinator.is_shade_available(self._shade.mac)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self._shade.mac)},
            connections={(dr.CONNECTION_NETWORK_MAC, self._shade.mac)},
            manufacturer="Wazombi Labs",
            name=self._shade.name,
            model=f"{self._shade.model[0]} {self._shade.model[1]}",
            sw_version=self.coordinator.soma_version,
        )
