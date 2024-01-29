"""Config flow for SOMA Connect."""

import logging

from aiohttp import ClientError
from aiosoma import SomaConnect
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 3000


class SomaConnectFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """Handle a config flow."""

    VERSION = 1

    def __init__(self):
        """Instantiate config flow."""

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        if user_input is None:
            data = {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }

            return self.async_show_form(step_id="user", data_schema=vol.Schema(data))

        return await self.async_step_creation(user_input)

    async def async_step_creation(self, user_input=None):
        """Finish config flow."""
        soma = SomaConnect(user_input["host"], user_input["port"])
        try:
            result = await soma.list_devices()
            _LOGGER.info("Successfully configured SOMA Connect")
            if result is not None:
                return self.async_create_entry(
                    title="SOMA Connect",
                    data={"host": user_input["host"], "port": user_input["port"]},
                )
            _LOGGER.error("Connection to SOMA Connect failed.")
            return self.async_abort(reason="result_error")

        except ClientError:
            _LOGGER.error("Connection to SOMA Connect failed with RequestException")
            return self.async_abort(reason="connection_error")

    async def async_step_import(self, user_input=None):
        """Handle flow start from existing config section."""
        if self._async_current_entries():
            return self.async_abort(reason="already_setup")

        return await self.async_step_creation(user_input)
