from atagmqtt.atag_interaction import AtagInteraction
from atagmqtt.configuration import Settings

from sys import exc_info
import logging

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=Settings().loglevel)

if __name__ == "__main__":
    loop = None
    interaction = AtagInteraction()
    interaction.main()