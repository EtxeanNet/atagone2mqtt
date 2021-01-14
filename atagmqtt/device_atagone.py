"""ATAG ONE device module."""
import logging
import asyncio

from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_setpoint import Property_Setpoint
from homie.node.property.property_boolean import Property_Boolean
from homie.node.property.property_temperature import Property_Temperature
from homie.node.property.property_integer import Property_Integer
from homie.node.property.property_float import Property_Float
from homie.node.property.property_enum import Property_Enum

from pyatag import AtagOne
from .configuration import Settings


LOGGER = logging.getLogger(__name__)
SETTINGS = Settings()

TRANSLATED_MQTT_SETTINGS = {
    'MQTT_BROKER': SETTINGS.mqtt_host,
    'MQTT_PORT': SETTINGS.mqtt_port,
    'MQTT_USERNAME' : SETTINGS.mqtt_username,
    'MQTT_PASSWORD' : SETTINGS.mqtt_password,
    'MQTT_CLIENT_ID' : SETTINGS.mqtt_client,
    'MQTT_SHARE_CLIENT': False,
}

TRANSLATED_HOMIE_SETTINGS = {
    'topic' : SETTINGS.homie_topic,
    'fw_name' : SETTINGS.homie_fw_name,
    'fw_version' : SETTINGS.homie_fw_version,
    'update_interval' : SETTINGS.homie_update_interval,
}

class DeviceAtagOne(Device_Base):
    """The ATAG ONE device."""
    def __init__(self, atag: AtagOne, eventloop, device_id="atagone", name="Atag One"):
        """Create an ATAG ONE Homie device."""
        super().__init__(device_id, name, TRANSLATED_HOMIE_SETTINGS, TRANSLATED_MQTT_SETTINGS)
        self.atag: AtagOne = atag
        self.temp_unit = atag.climate.temp_unit
        self._eventloop = eventloop

        LOGGER.debug("Setting up Homie nodes")
        node = (Node_Base(self, 'burner', 'Burner', 'status'))
        self.add_node(node)

        self.burner_modulation = Property_Integer(
            node, id="modulation", name="Burner modulation", settable=False)
        node.add_property(self.burner_modulation)

        self.burner_target = Property_Enum(
            node, id="target", name="Burner target", settable=False, data_format="none,ch,dhw")
        node.add_property(self.burner_target)

        # Central heating status properties
        node = (Node_Base(self, 'centralheating', 'Central heating', 'status'))
        self.add_node(node)

        self.ch_status = Property_Boolean(node, id="status", name="CH status", settable=False)
        node.add_property(self.ch_status)

        self.ch_temperature = Property_Temperature(
            node, id="temperature", name="CH temperature",
            settable=False, value=self.atag.climate.temperature,
            unit=self.temp_unit)
        node.add_property(self.ch_temperature)

        self.ch_water_temperature = Property_Temperature(
            node, id="water-temperature", name="CH water temperature",
            settable=False, value=self.atag.report["CH Water Temperature"].state,
            unit=self.temp_unit)
        node.add_property(self.ch_water_temperature)

        self.ch_target_water_temperature = Property_Temperature(
            node, id="target-water-temperature", name="CH target water temperature",
            settable=False, value=self.atag.climate.target_temperature,
            unit=self.temp_unit)
        node.add_property(self.ch_target_water_temperature)

        self.ch_return_water_temperature = Property_Temperature(
            node, id="return-water-temperature", name="CH return water temperature",
            settable=False, value=self.atag.report["CH Return Temperature"].state,
            unit=self.temp_unit)
        node.add_property(self.ch_return_water_temperature)

        self.ch_water_pressure = Property_Float(
            node, id="water-pressure", name="CH water pressure",
            settable=False, value=self.atag.report["CH Water Pressure"].state,
            unit=self.temp_unit)
        node.add_property(self.ch_water_pressure)

        # Domestic hot water status properties
        node = (Node_Base(self, 'domestichotwater', 'Domestic hot water', 'status'))
        self.add_node(node)

        self.dhw_status = Property_Boolean(
            node, id="status", name="DHW status", settable=False)
        node.add_property(self.dhw_status)

        self.dhw_temperature = Property_Temperature(
            node, id="temperature", name="DHW temperature",
            settable=False, value=self.atag.dhw.temperature,
            unit=self.temp_unit)
        node.add_property(self.dhw_temperature)

        node = (Node_Base(self, 'weather', 'Weather', 'status'))
        self.add_node(node)

        self.weather_temperature = Property_Temperature(
            node, id="temperature", name="Weather temperature",
            settable=False, value=self.atag.report["weather_temp"].state,
            unit=self.temp_unit)
        node.add_property(self.weather_temperature)

        # Control properties
        node = (Node_Base(self, 'controls', 'Controls', 'controls'))
        self.add_node(node)

        ch_min_temp = 12
        ch_max_temp = 25
        ch_target_temperature_limits = f'{ch_min_temp}:{ch_max_temp}'
        self.ch_target_temperature = Property_Setpoint(
            node, id='ch-target-temperature', name='CH Target temperature',
            data_format=ch_target_temperature_limits,
            unit=self.temp_unit,
            value=self.atag.climate.target_temperature,
            set_value=self.set_ch_target_temperature)
        node.add_property(self.ch_target_temperature)

        dhw_min_temp = self.atag.dhw.min_temp
        dhw_max_temp = self.atag.dhw.max_temp
        dhw_target_temperature_limits = f'{dhw_min_temp}:{dhw_max_temp}'
        self.dhw_target_temperature = Property_Setpoint(
            node, id='dhw-target-temperature', name='DHW Target temperature',
            data_format=dhw_target_temperature_limits,
            unit=self.temp_unit, value=self.atag.dhw.target_temperature,
            set_value=self.set_dhw_target_temperature)
        node.add_property(self.dhw_target_temperature)

        hvac_values = "auto,heat"
        self.hvac_mode = Property_Enum(
            node, id='hvac-mode', name='HVAC mode',
            data_format=hvac_values,
            unit=self.temp_unit,
            value=self.atag.climate.hvac_mode,
            set_value=self.set_hvac_mode)
        node.add_property(self.hvac_mode)
        LOGGER.debug("Setting up Homie nodes")
        self.start()

    def set_ch_target_temperature(self, value):
        """Set target central heating temperature."""
        oldvalue = self.atag.climate.target_temperature
        LOGGER.info(f"Setting target CH temperature from {oldvalue} to {value} {self.temp_unit}")
        self.ch_target_temperature.value = value
        self._run_coroutine(self._async_set_ch_target_temperature(value))

    async def _async_set_ch_target_temperature(self, value):
        await self.atag.climate.set_temp(value)
        LOGGER.info(f"Succeeded setting target CH temperature to {value} {self.temp_unit}")

    def set_dhw_target_temperature(self, value):
        """Set target domestic hot water temperature."""
        oldvalue = self.atag.dhw.target_temperature
        LOGGER.info(f"Setting target DHW temperature from {oldvalue} to {value} {self.temp_unit}")
        self.dhw_target_temperature.value = value
        self._run_coroutine(self._async_set_dhw_target_temperature(value))

    async def _async_set_dhw_target_temperature(self, value):
        await self.atag.dhw.set_temp(value)
        LOGGER.info(f"Succeeded setting target DHW temperature to {value} {self.temp_unit}")

    def set_hvac_mode(self, value):
        """Set HVAC mode."""
        oldvalue = self.atag.climate.hvac_mode
        LOGGER.info(f"Setting HVAC mode from {oldvalue} to {value}")
        self.hvac_mode.value = value
        self._run_coroutine(self._async_set_hvac_mode(value))

    async def _async_set_hvac_mode(self, value):
        await self.atag.climate.set_hvac_mode(value)
        LOGGER.info(f"Succeeded setting HVAC mode to {value}")

    async def update(self):
        """Update device status from atag device."""
        await self.atag.update()
        LOGGER.debug("Updating from latest device report")
        self.burner_modulation.value = self.atag.climate.flame
        self.hvac_mode.value = self.atag.climate.hvac_mode

        self.ch_target_temperature.value = self.atag.climate.target_temperature
        self.ch_temperature.value = self.atag.climate.temperature
        self.ch_target_water_temperature.value = self.atag.climate.target_temperature
        self.ch_water_temperature.value = self.atag.report["CH Water Temperature"].state
        self.ch_water_pressure.value = self.atag.report["CH Water Pressure"].state
        self.ch_return_water_temperature.value = self.atag.report["CH Return Temperature"].state
        self.ch_status.value = "true" if self.atag.climate.status else "false"

        self.dhw_target_temperature.value = self.atag.dhw.target_temperature
        self.dhw_temperature.value = self.atag.dhw.temperature
        self.dhw_status.value = "true" if self.atag.dhw.status else "false"

        self.weather_temperature.value = self.atag.report["weather_temp"].state

        if self.atag.dhw.status:
            self.burner_target.value = "dhw"
        elif self.atag.climate.status:
            self.burner_target.value = "ch"
        else:
            self.burner_target.value = "none"

    def _run_coroutine(self, coroutine):
        asyncio.run_coroutine_threadsafe(coroutine, self._eventloop)
