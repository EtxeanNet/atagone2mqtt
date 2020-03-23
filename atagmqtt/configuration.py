import homie
import atagmqtt
from typing import Set
import logging
from pydantic import (
    BaseModel, BaseSettings, Field, validator
)

class Settings(BaseSettings):
    hostname: str = Field('atagmqtt', env='HOSTNAME')
    loglevel: str = Field('INFO', env='LOGLEVEL')
    
    atag_update_interval: int = Field(30, env='ATAG_UPDATE_INTERVAL') 
    atag_host: str = Field(None, env='ATAG_HOST')
    atag_paired: bool = Field(False, env='ATAG_PAIRED')
        
    mqtt_host: str = Field(None, env='MQTT_HOST')
    mqtt_port: int = Field(1883, env='MQTT_PORT')
    mqtt_username: str = Field(None, env='MQTT_USERNAME')
    mqtt_password: str = Field(None, env='MQTT_PASSWORD')

    homie_update_interval: int = 60
    homie_topic: str = Field('homie',env='HOMIE_TOPIC')
    homie_implementation: str = f"Atag One Homie {atagmqtt.__version__} Homie 3 Version {homie.__version__}"
    homie_fw_name: str = "AtagOne"
    homie_fw_version: str = atagmqtt.__package__

    @staticmethod
    @validator("loglevel")
    def validate_name(cls, value):
        upper = value.upper()
        if upper not in logging._nameToLevel:
            raise ValueError("Invalid logging level")
        return upper

    class Config:
        env_file = '.env'
