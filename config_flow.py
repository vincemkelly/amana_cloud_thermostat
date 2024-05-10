import voluptuous as vol 
import requests
import logging
import json
from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_EMAIL
from .const import DOMAIN

DOMAIN = 'amana_cloud_thermostat'

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Starting config_flow.py: %s")

class AmanaCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        _LOGGER.debug("Initializing Amana Cloud Thermostat component")
        self.user_input = {}
        self.devices = []

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("Starting async_step_users")
        errors = {}
        if user_input is not None:
            _LOGGER.debug("Starting user_input step")
            email = user_input.get('email')
            integrator_token = user_input.get('integrator_token')
            api_key = user_input.get('api_key')

            try:
                # Authenticate and get access token
                _LOGGER.debug("Amana Thermostat Setup - Authenticate and get access token")
                access_token = await self._authenticate(email, integrator_token, api_key)
                _LOGGER.debug("AccessToken Received in Main method and equals: %s", access_token)
                if not access_token:
                    raise Exception("Failed to obtain access token")

                # Fetch devices with the access token
                _LOGGER.debug("Amana Thermostat Setup - Successfully captured accessToken and now fetching devices %s")
                self.devices = await self._fetch_devices(access_token, api_key)
                _LOGGER.debug("self.devices: %s", self.devices)
                self.user_input = user_input
                _LOGGER.debug("self.user_input: %s", self.user_input)
                self.access_token = access_token  
                _LOGGER.debug("self.access_token: %s", self.access_token)
                return await self.async_step_select_device()
            except Exception as e:
                _LOGGER.debug("Amana Thermostat Setup - Issue with authentication or fetching devices")
                errors["base"] = "auth_error"
                if isinstance(e, requests.exceptions.HTTPError):
                    errors["base"] = "http_error"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required('email'): str,
                vol.Required('integrator_token'): str,
                vol.Required('api_key'): str,
            }),
            errors=errors
        )

    async def _authenticate(self, email, integrator_token, api_key):
        """Authenticate with the Amana API and return the access token."""
        url = 'https://integrator-api.daikinskyport.com/v1/token'
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        data = {
            'email': email,
            'integratorToken': integrator_token
        }
        session = async_get_clientsession(self.hass)
        try:
            _LOGGER.debug("Sending authentication request to %s with email %s", url, email)
            response = await session.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = await response.json()
            _LOGGER.debug("Authentication successful, received data: %s", result)
            _LOGGER.debug("AccessToken: %s", result.get('accessToken'))
            return result.get('accessToken')
        except Exception as e:
            _LOGGER.error("Authentication failed: %s", str(e))
            if hasattr(e, 'response'):
                _LOGGER.error("Response status: %s, Response text: %s", e.response.status, e.response.text)
            return None

    async def _fetch_devices(self, access_token,  api_key):
        """Fetch device data from the Amana API."""
        url = 'https://integrator-api.daikinskyport.com/v1/devices'
        headers = {
            "Authorization": f'Bearer {access_token}',
            "x-api-key": api_key
        }
        session = async_get_clientsession(self.hass)
        try:
            _LOGGER.debug("Sending authentication request to %s with accessToken %s", url, access_token)
            response = await session.get(url, headers=headers)
            response.raise_for_status()
            result = await response.json()
            _LOGGER.debug("Authentication successful, received devices: %s", result)
            for device_data in result:  # Iterate over the list
                location_name = device_data['locationName']
                devices = device_data['devices']  # Access the 'devices' list within each dictionary

                for device in devices:
                    device_id = device['id']
                    device_name = device['name']
                    device_model = device['model']
                    device_firmwareVersion = device['firmwareVersion']

            _LOGGER.debug("Devices in Location '%s': %s", location_name, devices)
            return devices
        except Exception as e:
            _LOGGER.error("Retrieving Devices failed: %s", str(e))
            if hasattr(e, 'response'):
                _LOGGER.error("Response status: %s, Response text: %s", e.response.status, e.response.text)
            return None

    async def async_step_select_device(self, user_input=None):
        """Allow the user to select a device."""
        _LOGGER.debug("Starting async_step_select_device  %s")
        errors = {}
        devices_dict = {
            device['id']: {
                'name': device['name'],
                'model': device['model'],
                'firmwareVersion': device['firmwareVersion']
            }
            for device in self.devices
        }
        if user_input is not None:
            _LOGGER.debug("Starting User Input is not None in async_step_select_device  %s")
            # _LOGGER.debug("user_input:  %s", user_input)
            device_id = user_input['device_id']
            await self.async_set_unique_id(device_id)
            _LOGGER.debug("Set Unique ID  %s", device_id)
            # _LOGGER.debug("Set device_id:  %s", device_id)
            # _LOGGER.debug("devices_dict: %s", devices_dict[device_id]['name'])
            device_name = devices_dict[device_id]['name']
            _LOGGER.debug("Set device_name:  %s", device_name)
            device_model = devices_dict[device_id]['model']
            _LOGGER.debug("Set device_model:  %s", device_model)
            device_firmwareVersion = devices_dict[device_id]['firmwareVersion']
            _LOGGER.debug("Set device_firmwareVersion:  %s", device_firmwareVersion)
            # _LOGGER.debug("self %s", self)
            # Combine user input from previous step with device selection
            full_data = {**self.user_input, 'device_id': device_id, 'access_token': self.access_token, 'device_name': device_name, 'device_model': device_model, 'device_firmwareVersion': device_firmwareVersion}
            _LOGGER.debug("Full Data variable  %s", full_data)
            return self.async_create_entry(title="Amana Cloud Thermostat", data=full_data)
        # devices_dict = {device['id']: device['name'] for device in self.devices}
        
        # _LOGGER.debug("devices_dict: %s", devices_dict) 
        # _LOGGER.debug("devices_dict type: %s", type(devices_dict))
        # devices_dictKey = list(devices_dict.keys())[0]
        # _LOGGER.debug("devices_dictKey: %s", devices_dictKey)
        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({
                # vol.Required('device_id', default=lambda: list(devices_dict.keys())[0]): vol.All(vol.In(devices_dict), vol.Coerce(str))
                vol.Required('device_id', description='Choose your device:'): vol.In(list(devices_dict.keys()))
                # vol.Optional('name'): vol.Any(str, msg="Device name cannot be changed"),
                # vol.Optional('model'): vol.Any(str, msg="Device model is informational"),
                # vol.Optional('firmwareVersion'): vol.Any(str, msg="device_firmwareVersion is informational") 
            }),
            errors=errors
        )

_LOGGER.debug("About  to start the async_setup_entry in config_flow.py %s")
async def async_setup_entry(self, hass):
#     """Set up the Amana Thermostat climate platform based on a config entry."""
    _LOGGER.debug("Set up the Amana Thermostat climate platform based on a config entry. %s")

#     # Retrieve configuration details
#     email = entry.data.get('email')
#     api_key = entry.data.get('api_key')
#     access_token = entry.data.get('access_token')
#     device_id = entry.data.get('device_id')
#     integrator_token = entry.data.get('integrator_token')

#     # Retrieve the existing coordinator
#     coordinator = hass.data[DOMAIN][entry.entry_id]  

#     # Create and register the thermostat entity
#     async_add_entities([AmanaThermostat(coordinator)])  
