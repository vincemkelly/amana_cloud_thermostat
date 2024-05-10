"""Example integration using DataUpdateCoordinator."""

from datetime import timedelta
import logging
import json
import async_timeout
import asyncio


from homeassistant.components.climate import ClimateEntity
# from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (HomeAssistant, callback)
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from .api import amanaCloudDeviceAPI
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Starting coordinator.py: %s")


UPDATE_DELAY_TIME = 8

class amanaCloudDeviceUpdateCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, api:amanaCloudDeviceAPI):
        
        self.platforms = []
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.api = api


    async def _async_update_data(self):
        _LOGGER.debug("Starting the _async_update_data function")
        try:
            async with async_timeout.timeout(10):
                # listening_idx = set(self.async_contexts())
                # _LOGGER.debug("listening_idx: %s", listening_idx)
                response = await self.api.get_device_data()
                _LOGGER.debug("Response from _async_update_data %s", response)
                return json.loads(response)
        except Exception as exception:
            _LOGGER.debug("Response from _async_update_data %s", exception)
            raise UpdateFailed() from exception
        # except ApiAuthError as err:
        #     # Raising ConfigEntryAuthFailed will cancel future updates
        #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #     raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}"