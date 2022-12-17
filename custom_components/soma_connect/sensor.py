"""Support for Soma sensors."""
from datetime import timedelta
import logging

from aiosoma import Shade

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, LIGHT_LUX
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from . import DEVICES, SomaConnectEntity
from .const import SOMA, DOMAIN

SCAN_INTERVAL = timedelta(minutes=5)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soma sensor platform."""

    soma = hass.data[DOMAIN][SOMA]
    devices = hass.data[DOMAIN][DEVICES]

    async_add_entities(
        [
            SomaConnectBatterySensor(
                shade=Shade(soma, **shade), soma=hass.data[DOMAIN][SOMA]
            )
            for shade in devices
        ],
        True,
    )
    async_add_entities(
        [
            SomaConnectLightSensor(
                shade=Shade(soma, **shade), soma=hass.data[DOMAIN][SOMA]
            )
            for shade in devices
        ],
        True,
    )


class SomaConnectBatterySensor(SomaConnectEntity, SensorEntity):
    """Representation of a Soma cover device."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self.shade.name} battery level"

    @property
    def unique_id(self):
        return f"{self.shade.mac}_battery_level"

    @property
    def native_value(self):
        """Return the state of the entity."""
        return self.battery_state

    async def async_update(self) -> None:
        """Update the sensor with the latest data."""
        self.battery_state = await self.async_get_battery_level()


class SomaConnectLightSensor(SomaConnectEntity, SensorEntity):
    """Representation of a Soma cover device."""

    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    _attr_native_unit_of_measurement = LIGHT_LUX
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self.shade.name} light level"

    @property
    def unique_id(self):
        return f"{self.shade.mac}_light_level"

    @property
    def native_value(self):
        """Return the state of the entity."""
        return self.light_level

    async def async_update(self) -> None:
        """Update the sensor with the latest data."""
        self.light_level = await self.async_get_light_level()
