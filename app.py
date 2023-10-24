"""The main app."""
import logging
import asyncio

from atagmqtt.atag_interaction import main
from atagmqtt.configuration import Settings

logging.basicConfig(level=Settings().loglevel, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logging.getLogger('pyatag').setLevel(Settings().loglevel)
logging.getLogger('homie').setLevel(Settings().loglevel)
logging.getLogger('homie.device_base').setLevel(logging.INFO)
logging.getLogger('homie.node').setLevel(logging.INFO)

if __name__ == "__main__":
    asyncio.run(main())
