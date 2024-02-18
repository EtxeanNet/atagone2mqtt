"""The main app."""
import logging
import asyncio

from atagmqtt.__main__ import main
from atagmqtt.settings import Settings



if __name__ == "__main__":
    asyncio.run(main())
