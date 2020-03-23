# atagone-mqtt-bridge
An app to control and monitor an Atag One thermostat via Python/Docker

## Introduction

atagone-mqtt-bridge works as an bridge between the Atag One webapi and MQTT. It periodically polls the Atag One thermostat 
and publishes the sensor information to an MQTT broker. Reversely, it subscribes to control messages on a number of MQTT topics
and controls the Atag One thermostat e.g. to change the central heating or water setpoints.

The MQTT topics that the bridge follow the [Homie convention](https://homieiot.github.io/). By this means the Atag One can 
be integrated easily with home automation systems that recognize this convention such as [openHAB](https://www.openhab.org/) 
or [HomeAssistant](https://github.com/nerdfirefighter/HA_Homie/tree/dev). 

Under the hood, this bridge uses (a modified version of) the [pyatag](https://github.com/MatsNl/pyatag) library to interface 
with the Atag One Thermostat and the [homie v3](https://github.com/mjcumming/HomieV3) library to communicate with 
the MQTT broker.

## Setup

The configuration of atagone-mqtt-bridge is done with the following environment variables. 

`MQTT_HOST`
: The address of the MQTT broker.

`MQTT_USERNAME`
: Only use you need to use a username to connect to your MQTT broker.

`MQTT_PASSWORD`
: Only use you need this to connect to your MQTT broker.

`ATAG_HOST`
: The address of your Atag One  MQTT broker.
