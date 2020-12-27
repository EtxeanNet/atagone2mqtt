"""The main app."""
import logging
import asyncio

from atagmqtt.atag_interaction import main
from atagmqtt.configuration import Settings

logging.basicConfig(level=Settings().loglevel)

if __name__ == "__main__":
    asyncio.run(main())

