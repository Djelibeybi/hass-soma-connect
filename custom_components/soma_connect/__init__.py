"""Support for Soma Smartshades."""
import logging

from aiosoma import Connect, Shade

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, HOST, PORT, SOMA


_LOGGER = logging.getLogger(__name__)

DEVICES = "devices"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Required(CONF_HOST): cv.string, vol.Required(CONF_PORT): cv.string}
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = [Platform.COVER, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Soma component."""
    if DOMAIN not in config:
        return True

    _LOGGER.debug("Setting up SOMA Shades from YAML.")
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            data=config[DOMAIN],
            context={"source": config_entries.SOURCE_IMPORT},
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Soma from a config entry."""
    _LOGGER.debug("Setting up SOMA Shades from config entry.")

    hass.data[DOMAIN] = {}
    soma = Connect(entry.data[HOST], entry.data[PORT])
    hass.data[DOMAIN][SOMA] = soma
    devices = await soma.list_devices()
    hass.data[DOMAIN][DEVICES] = devices["shades"]

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


class SomaConnectEntity(Entity):
    """Representation of SOMA Connect shade."""

    def __init__(self, shade: Shade, soma: Connect):
        """Initialize the Soma device."""
        self.shade = shade
        self.soma = soma
        self.current_position = 50
        self.battery_state = 0
        self.light_level = 0
        self.is_available = True
        self.api_is_available = True

    @property
    def available(self):
        """Return true if the last API commands returned successfully."""
        return self.is_available

    @property
    def unique_id(self):
        """Return the unique id base on the id returned by pysoma API."""
        return self.shade.mac

    @property
    def name(self):
        """Return the name of the device."""
        return self.shade.name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.shade.mac)},
            connections={(dr.CONNECTION_NETWORK_MAC, self.shade.mac)},
            manufacturer="Wazombi Labs",
            name=self.shade.name,
            model=self.shade.model,
            hw_version=self.shade.gen,
        )

    def set_position(self, position: int) -> None:
        """Set the current device position."""
        self.current_position = int(position)
        self.schedule_update_ha_state()

    async def async_get_position(self) -> int | None:
        """Return the shade state."""
        result = await self.shade.get_state()
        _LOGGER.debug(
            "Updated position to %i for %s (%s)",
            result.get("position"),
            self.shade.name,
            self.shade.mac,
        )
        return int(result.get("position", None)) or None

    async def async_get_battery_level(self) -> int | None:
        """Return the battery level."""
        response = await self.shade.get_battery_level()
        battery_state: int | None = None


        # https://support.somasmarthome.com/hc/en-us/articles/360026064234-HTTP-API
        # The battery_level endpoint also returns battery_percentage with values
        # in the range 0..100 that should match what the SOMA app shows
        if (battery_percentage := response.get("battery_percentage", None)) is not None:
            battery_state = battery_percentage

        # battery_level response is expected to be min = 360, max 410 for
        # 0-100% levels above 410 are consider 100% and below 360, 0% as the
        # device considers 360 the minimum to move the motor.
        elif (battery_level := response.get("battery_level", None)) is not None:
            battery_state = max(min(100, round(2 * (int(battery_level) - 360))), 0)

        _LOGGER.debug(
            "Updating battery_level to %i for %s (%s)",
            battery_state,
            self.shade.name,
            self.shade.mac,
        )
        return int(battery_state) or None

    async def async_get_light_level(self) -> int | None:
        """Return the light level."""
        light_level: int | None = None

        result = await self.shade.get_light_level()
        light_level = result.get("light_level", None)

        _LOGGER.debug(
            "Updated light_level to %i for %s (%s)",
            light_level,
            self.shade.name,
            self.shade.mac,
        )

        return int(light_level) or None
