import logging
import asyncio

from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_setpoint import Property_Setpoint
from homie.node.property.property_boolean import Property_Boolean
from homie.node.property.property_temperature import Property_Temperature
from homie.node.property.property_integer import Property_Integer
from homie.node.property.property_float import Property_Float
from homie.node.property.property_string import Property_String
from pyatag import AtagDataStore
from configuration import MQTT_CONFIGURATION, HOMIE_SETTINGS

LOGGER = logging.getLogger(__name__)

translated_mqtt_settings = {
    'MQTT_BROKER': MQTT_CONFIGURATION['host'],
    'MQTT_PORT': MQTT_CONFIGURATION.get('port',1883),
    'MQTT_USERNAME' : MQTT_CONFIGURATION.get('username',None),
    'MQTT_PASSWORD' : MQTT_CONFIGURATION.get('password',None),
    'MQTT_CLIENT_ID' : 'homie',
    'MQTT_SHARE_CLIENT': False,
}

class Device_AtagOne(Device_Base):

    def __init__(self, atag: AtagDataStore, eventloop, device_id="atagone", name=None, homie_settings=HOMIE_SETTINGS, mqtt_settings=translated_mqtt_settings):
        super().__init__ (device_id, name, homie_settings, mqtt_settings)
        self._eventloop = eventloop
        self.atag: AtagDataStore = atag
        self.temp_unit = "°C"

        node = (Node_Base(self,'internals','Internals','status'))
        self.add_node (node)

        self.burner_modulation = Property_Integer(node,id="burner-modulation", name="Burner modulation", settable=False)
        node.add_property(self.burner_modulation)

        # Central heating status properties
        node = (Node_Base(self,'centralheating','Central heating','status'))
        self.add_node (node)

        self.ch_status = Property_Boolean(node,id="status", name="CH status", settable=False, value = self.atag.cv_status)
        node.add_property(self.ch_status)

        self.ch_temperature = Property_Temperature(node,id="temperature", name="CH temperature", settable=False, value = self.atag.temperature)
        node.add_property(self.ch_temperature)

        self.ch_water_temperature = Property_Temperature(node,id="water-temperature", name="CH water temperature", settable=False, value = self.atag.sensordata['ch_water_temp'].get('state',0))
        node.add_property(self.ch_water_temperature)

        self.ch_target_water_temperature = Property_Temperature(node,id="target-water-temperature", name="CH target water temperature", settable=False, value = self.atag.sensordata['ch_setpoint'].get('state',0))
        node.add_property(self.ch_target_water_temperature)

        self.ch_return_water_temperature = Property_Temperature(node,id="return-water-temperature", name="CH return water temperature", settable=False, value = self.atag.sensordata['ch_return_temp'].get('state',0))
        node.add_property(self.ch_return_water_temperature)

        self.ch_water_pressure = Property_Float(node,id="water-pressure", name="CH water pressure", settable=False, value = self.atag.sensordata['ch_water_pres'].get('state',0))
        node.add_property(self.ch_water_pressure)

        # Domestic hot water status properties
        node = (Node_Base(self,'domestichotwater','Domestic hot water','status'))
        self.add_node (node)

        self.dhw_status = Property_Boolean(node,id="status", name="DHW status", settable=False, value = self.atag.dhw_status)
        node.add_property(self.dhw_status)

        self.dhw_temperature = Property_Temperature(node,id="temperature", name="DHW temperature", settable=False, value = self.atag.dhw_temperature)
        node.add_property(self.dhw_temperature)

        node = (Node_Base(self,'weather','Weather','status'))
        self.add_node (node)

        self.weather_temperature = Property_Temperature(node,id="temperature", name="Weather temperature", settable=False, value = self.atag.sensordata['weather_temp'].get('state',0))
        node.add_property(self.weather_temperature)

        # Control properties
        node = (Node_Base(self,'controls','Controls','controls'))
        self.add_node(node)

        min_temp = 10
        max_temp = 25
        ch_target_temperature_limits = f'{min_temp}:{max_temp}'
        self.ch_target_temperature = Property_Setpoint(node,id='ch-target-temperature',name='CH Target temperature', 
            data_format=ch_target_temperature_limits, 
            unit=self.temp_unit,
            value = self.atag.target_temperature,
            set_value = lambda value: self.set_ch_target_temperature(value))
        node.add_property(self.ch_target_temperature)
        
        dhw_target_temperature_limits = f'0:65'
        self.dhw_target_temperature = Property_Setpoint(node,id='dhw-target-temperature',name='DHW Target temperature', 
            data_format=dhw_target_temperature_limits, 
            unit=self.temp_unit,
            value = self.atag.dhw_target_temperature,
            set_value = lambda value: self.set_dhw_target_temperature(value))
        node.add_property(self.dhw_target_temperature)

        self.hvac_mode = Property_String(node,id='hvac-mode',name='HVAC mode', 
            value = self.atag.hvac_mode,
            set_value = lambda value: self.set_hvac_mode(value))
        node.add_property(self.hvac_mode)
        
        self.start()

    def set_ch_target_temperature(self,value):
        oldvalue = self.ch_target_temperature.value
        LOGGER.info(f"Setting target CH temperature from {oldvalue} to {value} {self.temp_unit}")
        self.ch_target_temperature.value = value
        self._eventloop.create_task(self._async_set_ch_target_temperature(value))
                
    async def _async_set_ch_target_temperature(self,value):
        success = await self.atag.set_temp(value)
        if success:
            LOGGER.info(f"Succeeded setting target CH temperature to {value} {self.temp_unit}")

    def set_dhw_target_temperature(self,value):
        oldvalue = self.dhw_target_temperature.value
        LOGGER.info(f"Setting target DHW temperature from {oldvalue} to {value} {self.temp_unit}")
        self.dhw_target_temperature.value = value
        self._eventloop.create_task(self._async_set_dhw_target_temperature(value))

    async def _async_set_dhw_target_temperature(self,value):
        success = await self.atag.dhw_set_temp(value)
        if success:
            LOGGER.info(f"Succeeded setting target DHW temperature to {value} {self.temp_unit}")
    
    def set_hvac_mode(self,value):
        oldvalue = self.hvac_mode
        LOGGER.info(f"Setting HVAC mode from {oldvalue} to {value}")
        self.hvac_mode.value = value
        self._eventloop.create_task(self._async_set_hvac_mode(value))

    async def _async_set_hvac_mode(self,value):
        success = await self.atag.set_hvac_mode(value)
        if success:
            LOGGER.info(f"Succeeded setting HVAC mode to {value}")

    def update(self):
        LOGGER.debug("Updating from latest device report")
        self.burner_modulation.value           = self.atag.burner_status[1].get('state',0) if self.atag.burner_status[0] else 0
        self.hvac_mode.value                   = self.atag.hvac_mode

        self.ch_target_temperature.value       = self.atag.target_temperature
        self.ch_status.value                   = self.atag.cv_status
        self.ch_temperature.value              = self.atag.temperature
        self.ch_water_temperature.value        = self.atag.sensordata['ch_water_temp'].get('state',0)
        self.ch_water_pressure.value           = self.atag.sensordata['ch_water_pres'].get('state',0)
        self.ch_target_water_temperature.value = self.atag.sensordata['ch_setpoint'].get('state',0)
        self.ch_return_water_temperature.value = self.atag.sensordata['ch_return_temp'].get('state',0)

        self.dhw_target_temperature.value      = self.atag.dhw_target_temperature
        self.dhw_temperature.value             = self.atag.dhw_temperature
        self.dhw_status.value                  = self.atag.dhw_status

        self.weather_temperature.value         = self.atag.sensordata['weather_temp'].get('state',0)
        
        

