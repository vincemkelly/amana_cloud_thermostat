# from homeassistant.components.sensor import SensorEntity
# from homeassistant.const import PERCENTAGE
# import requests

# from .const import DOMAIN

# def get_device_data(api_key, device_id):
#     """Fetch device data from the Amana API."""
#     url = f"https://integrator-api.daikinskyport.com/v1/devices/{device_id}"
#     headers = {
#         "Authorization": f'Bearer {access_token}',
#         "x-api-key": api_key
#     }
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         raise Exception(f"Failed to fetch data: {response.status_code}")

# class AmanaThermostatTemperatureSensor(SensorEntity):
#     """Representation of a Temperature Sensor for Amana Thermostat."""

#     def __init__(self, hass, device_id, name, data_key):
#         """Initialize the sensor."""
#         self._hass = hass
#         self.api_key = api_key
#         self.access_token = access_token
#         self._device_id = device_id
#         self._name = f"{name} Temperature"
#         self._data_key = data_key
#         self._state = None

#     @property
#     def name(self):
#         """Return the name of the sensor."""
#         return self._name

#     @property
#     def unique_id(self):
#         """Return a unique ID."""
#         return f"{self._device_id}_{self._data_key}"

#     @property
#     def state(self):
#         """Return the current state."""
#         return self._state

#     @property
#     def unit_of_measurement(self):
#         """Return the unit of measurement."""
#         return TEMP_CELSIUS

#     def update(self):
#         """Fetch new state data for the sensor."""
#         # This should interact with your device to fetch the latest data
#         data = self._hass.data[DOMAIN][self._device_id]["data"]
#         self._state = data.get(self._data_key)
