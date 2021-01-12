"""Configuration module."""
import os

from pydantic import BaseSettings, Field
import homie
import atagmqtt
from .__init__ import __version__, NAME

HOSTNAME = os.getenv("HOSTNAME")

class Settings(BaseSettings):
    """Application settings for the ATAG ONE MQTT bridge."""

    hostname: str = Field('atagmqtt', env='HOSTNAME')
    loglevel: str = Field('INFO', env='LOGLEVEL')

    atag_setup_timeout: int = Field(30, env='ATAG_SETUP_TIMEOUT')

    atag_update_interval: int = Field(30, env='ATAG_UPDATE_INTERVAL')
    atag_host: str = Field(None, env='ATAG_HOST')
    atag_paired: bool = Field(False, env='ATAG_PAIRED')

    mqtt_host: str = Field(None, env='MQTT_HOST')
    mqtt_port: int = Field(1883, env='MQTT_PORT')
    mqtt_username: str = Field(None, env='MQTT_USERNAME')
    mqtt_password: str = Field(None, env='MQTT_PASSWORD')
    mqtt_client: str = Field(f"{NAME}-{HOSTNAME}", env='MQTT_CLIENT')

    homie_update_interval: int = 60
    homie_topic: str = Field('homie', env='HOMIE_TOPIC')
    homie_implementation: str \
        = f"Atag One Homie {atagmqtt.__version__} Homie 3 Version {homie.__version__}"
    homie_fw_name: str = "AtagOne"
    homie_fw_version: str = __version__

    class Config:
        """Where to find the environment file containing the settings."""

        env_file = '.env'
