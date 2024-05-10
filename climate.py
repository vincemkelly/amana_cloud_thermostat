from homeassistant.components.climate import (
    FAN_OFF,
    FAN_ON,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode
)
from homeassistant.components.persistent_notification import create
from homeassistant.core import HomeAssistant
from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import amanaCloudDeviceUpdateCoordinator
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
import asyncio
from .api import amanaCloudDeviceAPI
from .const import DOMAIN, MANUFACTURER
from homeassistant.components.climate.const import HVACMode
import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Starting climate.py: %s")

HVAC_MODE_MAP = {
    HVACMode.OFF: 0,
    HVACMode.HEAT: 1,
    HVACMode.COOL: 2,
    HVACMode.HEAT_COOL: 3,
    HVACMode.FAN_ONLY: 'fan_api_call'
}

FAN_MODE_MAP = {
    FAN_OFF: 'fan_off_call',
    FAN_ON: 0,
    FAN_LOW: 0,
    FAN_MEDIUM: 1,
    FAN_HIGH: 2,
}

_LOGGER.debug("About  to start the async_setup_entry in climate.py %s")
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    _LOGGER.debug("Starting async_setup_entry in climate.py: %s")
    api = hass.data[DOMAIN][entry.entry_id]
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    await coordinator.async_config_entry_first_refresh()

    _LOGGER.debug("entry.data: %s", entry.data)
    device_unique_id = entry.unique_id
    email = entry.data.get('email')
    integrator_token = entry.data.get('integrator_token')
    api_key = entry.data.get('api_key')
    access_token = entry.data.get('access_token')
    device_name = entry.data.get('device_name')
    device_model = entry.data.get('device_model')
    device_firmwareVersion = entry.data.get('device_firmwareVersion')
    # _LOGGER.debug("device_unique_id: %s", device_unique_id)
    my_climate_entity = AmanaThermostat(coordinator, device_unique_id, api_key, access_token, integrator_token, email, device_name, device_model, device_firmwareVersion)
    async_add_entities([my_climate_entity])

    return True

class AmanaThermostat(CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = None

    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator: amanaCloudDeviceUpdateCoordinator, device_unique_id, api_key, access_token, integrator_token, email,  device_name, device_model, device_firmwareVersion):
        _LOGGER.debug("__init__ within the AmanaThermostat Class: %s")
        """Initialize the thermostat."""
        super().__init__(coordinator)
        _LOGGER.debug("Initialized the thermostat. Coordinater.data: %s", self.coordinator.data)
        _LOGGER.debug("Initialized the thermostat. Coordinater.data: %s", type(self.coordinator.data))
        self._attr_unique_id = device_unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_unique_id)},
            name=f"Amana Thermostat - {device_name}",
            manufacturer=MANUFACTURER,
            model=device_model,
            sw_version=device_firmwareVersion
        )
        self.integrator_token = integrator_token
        self.email = email
        self.api_key = api_key
        self.access_token = access_token
        self.device_data = self.coordinator.data
        self.api = amanaCloudDeviceAPI(self._attr_unique_id, access_token, api_key, integrator_token, email)
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE_RANGE |
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )
        _LOGGER.debug(" self.api: %s", self.api)
        _LOGGER.debug("self.device_data: %s",  self.device_data)
        _LOGGER.debug("Completing AmanaThermostat init %s")

    def update_from_latest_data(self): 
        """Update the entity state from the latest data."""
        _LOGGER.debug("Starting update_from_latest_data in climate.py: %s")
        self._attr_current_temperature = self.device_data.get('current_temp') 
        self._attr_target_temperature = self.device_datadata.get('target_temp')   
        self._attr_hvac_mode = self.device_data.get('mode') 

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return (
                ClimateEntityFeature.TARGET_TEMPERATURE_RANGE |
                ClimateEntityFeature.FAN_MODE |
                ClimateEntityFeature.TURN_ON |
                ClimateEntityFeature.TURN_OFF
        )

    @property
    def hvac_mode(self):
        """Return current mode ie. heat, cool, idle."""
        if self.coordinator.data.get('equipmentStatus') == 5 and self.coordinator.data.get('mode') == 0:
            return HVACMode.OFF
        elif self.coordinator.data.get('mode') == 1:
            return HVACMode.HEAT
        elif self.coordinator.data.get('mode') == 2:
            return HVACMode.COOL
        elif self.coordinator.data.get('mode') == 3:
            return HVACMode.HEAT_COOL
        elif self.coordinator.data.get('equipmentStatus') == 4 and self.coordinator.data.get('mode') == 0:
            return HVACMode.FAN_ONLY

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL, HVACMode.FAN_ONLY]

    @property
    def hvac_action(self):
        """Return current action ie. heat, cool, idle."""
        if self.coordinator.data.get('equipmentStatus') == 5 and self.coordinator.data.get('mode') == 0:
            return HVACAction.OFF
        elif self.coordinator.data.get('equipmentStatus') == 3:
            return HVACAction.HEATING
        elif self.coordinator.data.get('equipmentStatus') == 1:
            return HVACAction.COOLING
        elif self.coordinator.data.get('equipmentStatus') == 4:
            return HVACAction.FAN
        elif self.coordinator.data.get('equipmentStatus') == 5:
            return HVACAction.IDLE

    @property
    def fan_mode(self):
        """Return current operation ie. heat, cool, idle."""
        if self.coordinator.data.get('fanCirculate') == 0:
            return FAN_OFF
        elif self.coordinator.data.get('fanCirculate') == 1 and self.coordinator.data.get('equipmentStatus') == 4:
            return FAN_ON
        # elif self.coordinator.data.get('fan') == 0:
        #     return FAN_AUTO
        if self.coordinator.data.get('fanCirculate') == 1 and self.coordinator.data.get('fanCirculateSpeed') == 0:
            return FAN_LOW
        elif self.coordinator.data.get('fanCirculate') == 1 and self.coordinator.data.get('fanCirculateSpeed') == 1:
            return FAN_MEDIUM
        elif self.coordinator.data.get('fanCirculate') == 1 and self.coordinator.data.get('fanCirculateSpeed') == 2:
            return FAN_HIGH

    @property
    def fan_modes(self):
        """Return the list of available operation modes."""
        return [FAN_OFF, FAN_ON, FAN_LOW, FAN_MEDIUM, FAN_HIGH]

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return "°C"

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self.coordinator.data.get('tempIndoor') is not None:
            return self.coordinator.data.get('tempIndoor')
        return None
    
    @property
    def current_humidity(self):
        """Return the current humidity."""
        if self.coordinator.data.get('humIndoor') is not None:
            return self.coordinator.data.get('humIndoor')
        return None

    @property
    def target_temperature_high(self):
        """Return the temperature we try to reach."""
        if self.coordinator.data.get('coolSetpoint') is not None:
            return self.coordinator.data.get('coolSetpoint')
        return None

    @property
    def max_temp(self):
        """Return the highest temperature that can be set."""
        if self.coordinator.data.get('setpointMaximum') is not None:
            return self.coordinator.data.get('setpointMaximum')
        return None

    @property
    def target_temperature_low(self):
        """Return the temperature we try to reach."""
        if self.coordinator.data.get('heatSetpoint') is not None:
            return self.coordinator.data.get('heatSetpoint')
        return None

    @property
    def min_temp(self):
        """Return the lowest temperature that can be set."""
        if self.coordinator.data.get('setpointMinimum') is not None:
            return self.coordinator.data.get('setpointMinimum')
        return None
    
    async def async_set_hvac_mode(self, hvac_mode): 
        _LOGGER.debug("Starting async_set_hvac_mode: %s", hvac_mode)
        heatSetpoint = self.coordinator.data.get('heatSetpoint')
        coolSetpoint = self.coordinator.data.get('coolSetpoint')
        _LOGGER.debug("hvac_mode: %s", hvac_mode)
        try:
            mode = HVAC_MODE_MAP[HVACMode(hvac_mode)]

            if mode == 'fan_api_call':
                _LOGGER.debug("Starting Call To Fan Only %s")
                fanCirculate = 1
                fanCirculateSpeed = 0
                await self.api.updateFanMode(fanCirculate, fanCirculateSpeed)
                mode = 0
                await self.api.updateThermostatMode(mode, heatSetpoint, coolSetpoint)
            else:
                _LOGGER.debug("Starting Call To HVAC_Modes not Fan Only %s")   
                await self.api.updateThermostatMode(mode, heatSetpoint, coolSetpoint)
        except (KeyError, APIError) as e:
            _LOGGER.error("Error setting HVAC mode: %s", e)
            return
        
        # Wait for 10 seconds per Amana API before repulling coordinator
        await asyncio.sleep(10)
        
    async def async_set_fan_mode(self, fan_mode):
        _LOGGER.debug("Starting async_set_fan_mode: %s", fan_mode)
        try:
            fanCirculateSpeed = FAN_MODE_MAP[fan_mode]
            if fanCirculateSpeed == 'fan_off_call':
                fanCirculate = 0
                fanCirculateSpeed = 0
                _LOGGER.debug("Variable fanCirculateSpeed: %s", fanCirculateSpeed)
                await self.api.updateFanMode(fanCirculate, fanCirculateSpeed)
            else:
                _LOGGER.debug("Starting Call To Fan Only Mode Change %s")
                fanCirculate = 1
                await self.api.updateFanMode(fanCirculate, fanCirculateSpeed)
        except (KeyError, APIError) as e:
            _LOGGER.error("Error setting HVAC mode: %s", e)
            return
        
        # Wait for 10 seconds per Amana API before repulling coordinator
        await asyncio.sleep(10)

    
    async def async_turn_on(self):
        heatSetpoint = self.coordinator.data.get('heatSetpoint')
        coolSetpoint = self.coordinator.data.get('coolSetpoint')
        _LOGGER.debug("Starting async_turn_on %s")
        try:
            mode = 3
            _LOGGER.debug("Starting Call To HVAC_Modes not Fan Only %s")   
            await self.api.updateThermostatMode(mode, heatSetpoint, coolSetpoint)
        except (KeyError, APIError) as e:
            _LOGGER.error("Error setting HVAC mode: %s", e)
            return
        
        # Wait for 10 seconds per Amana API before repulling coordinator
        await asyncio.sleep(10)
    
    async def async_turn_off(self):
        _LOGGER.debug("Starting async_turn_off %s")
        heatSetpoint = self.coordinator.data.get('heatSetpoint')
        coolSetpoint = self.coordinator.data.get('coolSetpoint')
        mode = 0
        fanCirculate = 0
        fanCirculateSpeed = 0
        try:
            _LOGGER.debug("Starting Call To turn off HVAC_Modes %s")   
            await self.api.updateThermostatMode(mode, heatSetpoint, coolSetpoint)
            _LOGGER.debug("Starting Call To turn off Fan %s")   
            await self.api.updateFanMode(fanCirculate, fanCirculateSpeed)
        except (KeyError, APIError) as e:
            _LOGGER.error("Error setting HVAC mode: %s", e)
            return
        
        # Wait for 10 seconds per Amana API before repulling coordinator
        await asyncio.sleep(10)
    
    async def async_set_temperature(self, **kwargs):
        _LOGGER.debug("Starting async_set_temperature %s")
        coolSetpoint = self.coordinator.data.get('coolSetpoint')
        _LOGGER.debug("coolSetpoint: %s", coolSetpoint)
        heatSetpoint = self.coordinator.data.get('heatSetpoint')
        _LOGGER.debug("heatSetpoint: %s", heatSetpoint)
        target_temp_low = round(kwargs.get('target_temp_low'), 1)
        _LOGGER.debug("target_temp_low: %s", target_temp_low)
        target_temp_high = round(kwargs.get('target_temp_high'), 1)
        _LOGGER.debug("target_temp_high: %s", target_temp_high)

        setpointDelta = self.coordinator.data.get('setpointDelta')

        if heatSetpoint != target_temp_low:
            heatSetpoint = target_temp_low
        _LOGGER.debug("coolSetpoint: %s", coolSetpoint)
        if coolSetpoint != target_temp_high:
            coolSetpoint = target_temp_high
        _LOGGER.debug("heatSetpoint: %s", heatSetpoint)

        currentSetpointDelta = coolSetpoint - heatSetpoint
        _LOGGER.debug("currentSetpointDelta: %s", currentSetpointDelta)

        if heatSetpoint > coolSetpoint:
            raise HomeAssistantError(f"Error settings temperature; Heat setpoint: {heatSetpoint} needs to be lower than the cool setpoint: {coolSetpoint} by setpoint delta: {setpointDelta}.")
        elif currentSetpointDelta < 2:
            raise HomeAssistantError(f"Error settings temperature; The current setPointDelta: {currentSetpointDelta} must be 2 or greater.")

        try:
            _LOGGER.debug("Starting Call To Change Temperature %s")
            _LOGGER.debug("heatSetpoint: %s", heatSetpoint)
            _LOGGER.debug("coolSetpoint: %s", coolSetpoint)
            mode = self.coordinator.data.get('mode')
            await self.api.updateThermostatMode(mode, heatSetpoint, coolSetpoint)
        except (KeyError, APIError) as e:
            _LOGGER.error("Error setting HVAC mode: %s", e)
            return
        
        # Wait for 10 seconds per Amana API before repulling coordinator
        await asyncio.sleep(10)