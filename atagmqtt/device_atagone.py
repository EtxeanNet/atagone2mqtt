import logging
import asyncio

from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_setpoint import Property_Setpoint
from homie.node.property.property_boolean import Property_Boolean
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

        # Status properties
        node = (Node_Base(self,'status','Status','status'))
        self.add_node (node)

        self.cv_status = Property_Boolean(node,id="cv-status", name="CV status", settable=False)
        node.add_property(self.cv_status)

        self.dhw_status = Property_Boolean(node,id="dhw-status", name="DHW status", settable=False)
        node.add_property(self.dhw_status)

        # Control properties
        node = (Node_Base(self,'controls','Controls','controls'))
        self.add_node(node)

        min_temp = 10
        max_temp = 25
        target_temperature_limits = f'{min_temp}:{max_temp}'
        self.target_temperature = Property_Setpoint(node,id='target-temperature',name='Target temperature', 
            data_format=target_temperature_limits, 
            unit=self.temp_unit,
            value = self.atag.target_temperature,
            set_value = lambda value: self.set_target_temperature(value))
        node.add_property(self.target_temperature)
        self.start()

    def set_target_temperature(self,value):
        oldvalue = self.target_temperature.value
        LOGGER.info(f"Setting target temperature from {oldvalue} to {value} {self.temp_unit}")
        self.target_temperature.value = value
        self._eventloop.create_task(self._async_set_target_temperature(value))
                
    async def _async_set_target_temperature(self,value):
        success = await self.atag.set_temp(value)
        if success:
            LOGGER.info(f"Succeeded setting target temperature to {value} {self.temp_unit}")
        
    def update(self):
        LOGGER.debug("Updating from latest device report")
        self.target_temperature.value = self.atag.target_temperature
        self.cv_status.value = self.atag.cv_status
        self.dhw_status.value = self.atag.dhw_status