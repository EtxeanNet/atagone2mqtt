import homie
import atagmqtt

ATAG_CONFIGURATION = {
    'host': '192.168.249.10',
    'hostname': 'atagmqtt',
    'update_interval': 30,
}

MQTT_CONFIGURATION = {
    'host': '192.168.249.5',
    # 'port': 1883,
    'username': 'etxeaniot',
    'password': 'AiYQQR6x7nXvRZp7yTEU',
}

HOMIE_SETTINGS = {
    "update_interval": 60,
    'topic' : 'homie',   
    "implementation": "Atag One Homie {} Homie 3 Version {}".format(
        atagmqtt.__version__,homie.__version__
    ),
    "fw_name": "AtagOne",
    "fw_version": atagmqtt.__package__,
}