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
from homie.node.property.property_string import Property_String

from pyatag import AtagOne
from pyatag.const import STATES
from .settings import Settings

logger = logging.getLogger(__name__)

class DeviceAtagOne(Device_Base):
    """The ATAG ONE device."""
    def __init__(self, atag: AtagOne, device_id="atagone", name="Atag One", settings: Settings = Settings()):
        """Create an ATAG ONE Homie device."""
        homie_settings = self._to_homie_settings(settings)
        mqtt_settings = self._to_mqtt_settings(settings)
        super().__init__(device_id, name, homie_settings, mqtt_settings)
        self.atag: AtagOne = atag
        self.temp_unit = atag.climate.temp_unit

        logger.debug("Setting up Homie nodes")
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

        ch_mode_values = ",".join(STATES["ch_mode"].values())
        self.ch_mode = Property_Enum(
            node, id="mode", name="CH mode",
            settable=False, value=self.atag.climate.preset_mode,
            data_format=ch_mode_values
            )
        node.add_property(self.ch_mode)

        self.ch_mode_duration = Property_String(
            node, id="mode-duration", name="CH mode duration",
            settable=False, value=self.atag.climate.preset_mode_duration,
            )
        node.add_property(self.ch_mode_duration)

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

        dhw_mode_values = ",".join(STATES["dhw_mode"].values()) + ",off"
        self.dhw_mode = Property_Enum(
            node, id="mode", name="DHW mode",
            settable=False, value=self.atag.dhw.current_operation,
            data_format=dhw_mode_values
            )
        node.add_property(self.dhw_mode)

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
            unit=self.temp_unit, value=max(self.atag.dhw.target_temperature, dhw_min_temp),
            set_value=self.set_dhw_target_temperature)
        node.add_property(self.dhw_target_temperature)

        hvac_values = ",".join(STATES["ch_control_mode"].values())
        self.hvac_mode = Property_Enum(
            node, id='hvac-mode', name='HVAC mode',
            data_format=hvac_values,
            unit=self.temp_unit,
            value=self.atag.climate.hvac_mode,
            set_value=self.set_hvac_mode)
        node.add_property(self.hvac_mode)

        ch_mode_values = ",".join(STATES["ch_mode"].values())
        self.ch_mode_control = Property_Enum(
            node, id="ch-mode", name="CH mode",
            data_format=ch_mode_values,
            value=self.atag.climate.preset_mode,
            set_value=self.set_ch_mode
            )
        node.add_property(self.ch_mode_control)

        logger.debug("Starting Homie device")
        self.start()

    def set_ch_target_temperature(self, value):
        """Set target central heating temperature."""
        oldvalue = self.atag.climate.target_temperature
        logger.info(f"Setting target CH temperature from {oldvalue} to {value} {self.temp_unit}")
        self.ch_target_temperature.value = value
        _async_to_sync(self._async_set_ch_target_temperature(value))

    async def _async_set_ch_target_temperature(self, value):
        await self.atag.climate.set_temp(value)
        logger.info(f"Succeeded setting target CH temperature to {value} {self.temp_unit}")

    def set_dhw_target_temperature(self, value):
        """Set target domestic hot water temperature."""
        oldvalue = self.atag.dhw.target_temperature
        logger.info(f"Setting target DHW temperature from {oldvalue} to {value} {self.temp_unit}")
        self.dhw_target_temperature.value = value
        _async_to_sync(self._async_set_dhw_target_temperature(value))

    async def _async_set_dhw_target_temperature(self, value):
        await self.atag.dhw.set_temp(value)
        logger.info(f"Succeeded setting target DHW temperature to {value} {self.temp_unit}")

    def set_hvac_mode(self, value):
        """Set HVAC mode."""
        oldvalue = self.atag.climate.hvac_mode
        logger.info(f"Setting HVAC mode from {oldvalue} to {value}")
        self.hvac_mode.value = value
        _async_to_sync(self._async_set_hvac_mode(value))

    async def _async_set_hvac_mode(self, value):
        await self.atag.climate.set_hvac_mode(value)
        logger.info(f"Succeeded setting HVAC mode to {value}")

    def set_ch_mode(self, value):
        """Set CH mode."""
        oldvalue = self.atag.climate.preset_mode
        logger.info(f"Setting CH mode from {oldvalue} to {value}")
        self.ch_mode_control.value = value
        self.ch_mode.value = value
        self._async_to_sync(self._async_set_ch_mode(value))

    async def _async_set_ch_mode(self, value):
        await self.atag.climate.set_preset_mode(value)
        logger.info(f"Succeeded setting CH mode to {value}")

    async def update(self):
        """Update device status from atag device."""
        await self.atag.update()
        logger.debug("Updating from latest device report")
        self.burner_modulation.value = self.atag.climate.flame
        self.hvac_mode.value = self.atag.climate.hvac_mode
        self.ch_mode.value = self.atag.climate.preset_mode
        self.ch_mode_duration.value = self.atag.climate.preset_mode_duration
        self.ch_mode_control.value = self.atag.climate.preset_mode

        self.ch_target_temperature.value = self.atag.climate.target_temperature
        self.ch_temperature.value = self.atag.climate.temperature
        self.ch_target_water_temperature.value = self.atag.climate.target_temperature
        self.ch_water_temperature.value = self.atag.report["CH Water Temperature"].state
        self.ch_water_pressure.value = self.atag.report["CH Water Pressure"].state
        self.ch_return_water_temperature.value = self.atag.report["CH Return Temperature"].state
        self.ch_status.value = True if self.atag.climate.status else False

        self.dhw_target_temperature.value = self.atag.report["dhw_temp_setp"].state
        self.dhw_temperature.value = self.atag.dhw.temperature
        self.dhw_status.value = True if self.atag.dhw.status else False
        self.dhw_mode.value = self.atag.dhw.current_operation

        self.weather_temperature.value = self.atag.report["weather_temp"].state

        if self.atag.dhw.status:
            self.burner_target.value = "dhw"
        elif self.atag.climate.status:
            self.burner_target.value = "ch"
        else:
            self.burner_target.value = "none"

    def _to_homie_settings(self, settings: Settings):
        return {
            'topic' : settings.homie_topic,
            'fw_name' : settings.homie_fw_name,
            'fw_version' : settings.homie_fw_version,
            'update_interval' : settings.homie_update_interval,
        }

    def _to_mqtt_settings(self, settings: Settings):
        return {
            'MQTT_BROKER': settings.mqtt_host,
            'MQTT_PORT': settings.mqtt_port,
            'MQTT_USERNAME' : settings.mqtt_username,
            'MQTT_PASSWORD' : settings.mqtt_password,
            'MQTT_CLIENT_ID' : settings.mqtt_client,
            'MQTT_SHARE_CLIENT': False,
        }
        
def _async_to_sync(awaitable):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(awaitable)