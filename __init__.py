from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import async_get_platforms 
from homeassistant.const import Platform
from datetime import timedelta 
from .const import DOMAIN, MANUFACTURER
import logging
from .api import amanaCloudDeviceAPI
from .coordinator import amanaCloudDeviceUpdateCoordinator

import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Starting init.py: %s")

PLATFORMS: list[str] = ["climate"]

async def async_setup(hass: HomeAssistant, config: Config):
    # """Set up configured Amana Cloud Thermostat."""
    # if DOMAIN not in config:
    #     return True

    # hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Amana Cloud Thermostat from a config entry."""
    _LOGGER.debug("About  to start the async_setup_entry in init.py %s")
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    # Retrieve user configuration from the config entry
    email = entry.data.get('email')
    integrator_token = entry.data.get('integrator_token')
    api_key = entry.data.get('api_key')
    access_token = entry.data.get('access_token')
    device_id = entry.data.get('device_id')
    device_name = entry.data.get('device_name')
    api = amanaCloudDeviceAPI(device_id, access_token, api_key, integrator_token, email)
    sync_interval = 300
    coordinator = amanaCloudDeviceUpdateCoordinator(
        hass, api
    )
    _LOGGER.debug("Setting up the coordinator %s", coordinator)
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data[DOMAIN]
    hass.data[DOMAIN][entry.entry_id] = coordinator
    _LOGGER.debug("Storing the coordinator %s", coordinator)

    # Create the device 
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        # self,
        config_entry_id=entry.entry_id,
        name=f"Amana Thermostat - {device_name}",
        manufacturer=MANUFACTURER, 
        model=entry.data.get('device_model'),
        sw_version=entry.data.get('device_firmwareVersion'),
        identifiers={(DOMAIN, device_id)}
        # ... other relevant device info... 
    )
    _LOGGER.debug("Completed device_registry.async_get_or_create  %s")

    # Register the platform and entities
    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            await hass.config_entries.async_forward_entry_setup(entry, platform)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Running the async_unload_entry in init.py%s")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok