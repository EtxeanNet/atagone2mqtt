''' The main app. '''
import logging
from atagmqtt.atag_interaction import AtagInteraction
from atagmqtt.configuration import Settings


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=Settings().loglevel)

if __name__ == "__main__":
    LOOP = None
    INTERACTION = AtagInteraction()
    INTERACTION.main()
