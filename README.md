# atagone2mqtt

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/fd572a99c73f429cb6aba7ac43776515)](https://www.codacy.com/gh/EtxeanNet/atagone2mqtt?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=EtxeanNet/atagone2mqtt&amp;utm_campaign=Badge_Grade)
![Docker Pulls](https://img.shields.io/docker/pulls/etxean/atagone2mqtt)
[![HitCount](https://hits.dwyl.com/EtxeanNet/atagone2mqtt.svg)](https://hits.dwyl.com/EtxeanNet/atagone2mqtt)

An app to control and monitor an Atag One thermostat via MQTT

## Introduction

**atagone2mqtt** works as an bridge between the Atag One webapi and MQTT. It periodically polls the Atag One thermostat and publishes the sensor information to an MQTT broker. Reversely, it subscribes to control messages on a number of MQTT topics and controls the Atag One thermostat e.g. to change the central heating or water setpoints.

The MQTT topics that this app publishes follow the [Homie convention](https://homieiot.github.io/). By this means the Atag One can be integrated easily with home automation systems that recognize this convention such as [openHAB](https://www.openhab.org/) or [HomeAssistant](https://github.com/nerdfirefighter/HA_Homie/tree/dev).

Under the hood, this bridge uses (a modified version of) the [pyatag](https://github.com/MatsNl/pyatag) library to interface with the Atag One Thermostat and the [Homie](https://github.com/mjcumming/Homie4) library to communicate with the MQTT broker.

## Setup

The configuration of atagone2mqtt is done with the following environment variables.

`MQTT_HOST`
: The address of the MQTT broker.

`MQTT_PORT`
: USe this if your MQTT broker uses a port different from 1883.

`MQTT_USERNAME`
: Only use this if you need to use a username to connect to your MQTT broker.

`MQTT_PASSWORD`
: Only use this if you need this to connect to your MQTT broker.

`MQTT_CLIENT`
: The name used to identify this client to the MQTT broker. If not specified, the client will announce itself as '&lt;atagmqtt-HOSTNAME&gt;'.

`ATAG_HOST`
: The address of your Atag One thermostat. If this is not specified then the Atag One themostat is discovered automatically on the local netwerk. Make sure that UDP port 11000 is not blocked by the firewall.

## Build

You can run the app directly from Python, after installing the modules with [poetry](https://python-poetry.org/docs/):

```bash
pip install poetry
poetry install --without dev --no-root
python -m atagmqtt
```

Alternatatively, you can use the supplied Dockerfile to build a Docker container to run app.

Building for docker hub can be done with:

```bash
docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag etxean/atagone2mqtt:<version> --tag etxean/atagone2mqtt:latest .
```
