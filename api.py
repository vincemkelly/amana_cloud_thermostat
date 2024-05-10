import aiohttp
import asyncio
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_LOGGER.debug("Starting the api.py: %s")

class amanaCloudDeviceAPI:
    def __init__(self, device_id, access_token, api_key, integrator_token, email):
        _LOGGER.debug("Starting init function in amanaCloudDeviceAPI class")
        self.device_id = device_id
        self.access_token = access_token
        self.api_key = api_key
        self.integrator_token = integrator_token
        self.email = email

    async def get_device_data(self,  max_retries=2) -> dict:
        _LOGGER.debug("Starting get_device_data function in amanaCloudDeviceAPI class")
        device_info_uri = 'https://integrator-api.daikinskyport.com/v1/devices/'+ self.device_id
        headers = {
                "Authorization": f'Bearer {self.access_token}',
                "x-api-key": self.api_key
            }
        _LOGGER.debug("headers %s", headers)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(device_info_uri, headers=headers) as response:
                    _LOGGER.debug("API Request Sent to: %s", device_info_uri)
                    response.raise_for_status()
                    data = await response.text()
                    _LOGGER.info("Device data successfully retrieved: %s", data)  
                    return data
            except Exception as e:
                if e.status == 401 and max_retries > 0:
                    _LOGGER.warning("401 Unauthorized. Attempting authorization refresh (retries left: %s)", max_retries)
                    await self.get_access_token ()
                    return await self.get_device_data(max_retries - 1)
                else:
                    _LOGGER.error("Error getting device data: %s", e) 
                    raise  # Re-raise other errors
            except Exception as e:  
                _LOGGER.exception("Unexpected error during data retrieval: %s", e)
                raise  # Re-raise to propagate the error
    

    async def get_access_token(self):
        _LOGGER.debug("Getting New Access Token")
        url = 'https://integrator-api.daikinskyport.com/v1/token'
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        data = {
            'email': self.email,
            'integratorToken': self.integrator_token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                _LOGGER.debug("API Access Token Request Sent to: %s", url)
                data = await response.json()
                _LOGGER.debug("API Access Token Response: %s", data.get('accessToken'))
                self.access_token = data.get('accessToken')
                _LOGGER.debug("AccessToken: %s", self.access_token)

    async def updateThermostatMode(self, mode, heatSetpoint, coolSetpoint,  max_retries=2) -> dict:
        _LOGGER.debug("Updating thermostat mode")
        url = f'https://integrator-api.daikinskyport.com/v1/devices/{self.device_id}/msp'
        headers = {
            'Content-Type': 'application/json',
            "Authorization": f'Bearer {self.access_token}',
            'x-api-key': self.api_key            
        }
        _LOGGER.debug("mode: %s", mode)
        _LOGGER.debug("heatSetpoint: %s", heatSetpoint)
        _LOGGER.debug("coolSetpoint: %s", coolSetpoint)
        data = {
            "mode": mode,
            "heatSetpoint": heatSetpoint,
            "coolSetpoint": coolSetpoint
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(url, headers=headers, json=data) as response:
                    _LOGGER.debug("Updating thermostat mode sent to: %s", url)
                    response.raise_for_status()
                    data = await response.text()
                    _LOGGER.info("Device data successfully retrieved: %s", data) 
                    return data
            except Exception as e:
                if e.status == 401 and max_retries > 0:
                    _LOGGER.warning("401 Unauthorized. Attempting authorization refresh (retries left: %s)", max_retries)
                    self._temp_mode = mode 
                    self._temp_heatSetpoint = heatSetpoint
                    self._temp_coolSetpoint = coolSetpoint
                    await self.get_access_token ()
                    return await self.updateThermostatMode(self._temp_mode, self._temp_heatSetpoint, self._temp_coolSetpoint, max_retries - 1)
                else:
                    _LOGGER.error("Error getting device data: %s", e) 
                    raise  # Re-raise other errors
            except Exception as e:  
                _LOGGER.exception("Unexpected error during data retrieval: %s", e)
                raise  # Re-raise to propagate the error

    async def updateFanMode(self, fanCirculate, fanCirculateSpeed,  max_retries=2) -> dict:
        _LOGGER.debug("Updating Fan mode")
        url = f'https://integrator-api.daikinskyport.com/v1/devices/{self.device_id}/fan'
        headers = {
            'Content-Type': 'application/json',
            "Authorization": f'Bearer {self.access_token}',
            'x-api-key': self.api_key            
        }
        _LOGGER.debug("fanCirculate: %s", fanCirculate)
        _LOGGER.debug("fanCirculateSpeed: %s", fanCirculateSpeed)
        data = {
            "fanCirculate": fanCirculate,
            "fanCirculateSpeed": fanCirculateSpeed
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(url, headers=headers, json=data) as response:
                    _LOGGER.debug("Updating fan mode sent to: %s", url)
                    response.raise_for_status()
                    data = await response.text()
                    _LOGGER.info("Device data successfully retrieved: %s", data) 
                    return data
            except Exception as e:
                if e.status == 401 and max_retries > 0:
                    _LOGGER.warning("401 Unauthorized. Attempting authorization refresh (retries left: %s)", max_retries)
                    self._temp_fanCirculate = fanCirculate 
                    self._temp_fanCirculateSpeed = fanCirculateSpeed
                    await self.get_access_token ()
                    return await self.updateFanMode(self._temp_fanCirculate, self._temp_fanCirculateSpeed, max_retries - 1)
                else:
                    _LOGGER.error("Error getting device data: %s", e) 
                    raise  # Re-raise other errors
            except Exception as e:  
                _LOGGER.exception("Unexpected error during data retrieval: %s", e)
                raise  # Re-raise to propagate the error