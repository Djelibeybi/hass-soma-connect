"""Sensor entities for SOMA Connect."""
from __future__ import annotations

from aiosoma import SomaShade

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import LIGHT_LUX, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SomaConnectUpdateCoordinator
from .entity import SomaConnectEntity

BATTERY_LEVEL_SENSOR = "battery_level"
LIGHT_LEVEL_SENSOR = "light_level"

BATTERY_SENSOR_DESCRIPTION = SensorEntityDescription(
    key=BATTERY_LEVEL_SENSOR,
    name="Battery",
    device_class=SensorDeviceClass.BATTERY,
    has_entity_name=True,
    native_unit_of_measurement=PERCENTAGE,
    entity_category=EntityCategory.DIAGNOSTIC,
)

LIGHT_SENSOR_DESCRIPTION = SensorEntityDescription(
    key=LIGHT_LEVEL_SENSOR,
    name="Light level",
    entity_registry_enabled_default=False,
    device_class=SensorDeviceClass.ILLUMINANCE,
    has_entity_name=True,
    native_unit_of_measurement=LIGHT_LUX,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soma sensor platform."""

    coordinator: SomaConnectUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SomaConnectBatterySensor | SomaConnectLightSensor] = []

    for shade in coordinator.shades:
        entities.append(
            SomaConnectBatterySensor(coordinator, shade, BATTERY_SENSOR_DESCRIPTION)
        )
        entities.append(
            SomaConnectLightSensor(coordinator, shade, LIGHT_SENSOR_DESCRIPTION)
        )

    async_add_entities(entities, True)


class SomaConnectBatterySensor(SomaConnectEntity, SensorEntity):
    """Representation of a Soma cover device."""

    def __init__(
        self,
        coordinator: SomaConnectUpdateCoordinator,
        shade: SomaShade,
        description: SensorEntityDescription,
    ) -> None:
        """Initialise the battery sensor."""
        super().__init__(coordinator, shade)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{shade.mac}_{description.key}"
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_native_value = shade.battery_percentage

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    def _async_update_attrs(self) -> None:
        """Update position attribute."""
        self._attr_native_value = self.coordinator.get_battery_level(self._shade.mac)


class SomaConnectLightSensor(SomaConnectEntity, SensorEntity):
    """Representation of a Soma cover device."""

    def __init__(
        self,
        coordinator: SomaConnectUpdateCoordinator,
        shade: SomaShade,
        description: SensorEntityDescription,
    ) -> None:
        """Initialise the light sensor."""
        super().__init__(coordinator, shade)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{shade.mac}_{description.key}"
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_native_value = shade.light_level

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    def _async_update_attrs(self) -> None:
        """Update position attribute."""
        self._attr_native_value = self.coordinator.get_light_level(self._shade.mac)

    @callback
    async def async_added_to_hass(self) -> None:
        """Enable sensor updates."""

        self.async_on_remove(
            await self.coordinator.async_enable_light_level_updates(self._shade.mac)
        )

        return await super().async_added_to_hass()
