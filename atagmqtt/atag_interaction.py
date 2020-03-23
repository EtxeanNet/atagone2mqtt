import asyncio
import logging
import time
import sys

from pyatag.gateway import AtagDataStore
from .device_atagone import Device_AtagOne
from .configuration import Settings

settings = Settings()

logger = logging.getLogger(__name__)

class AtagInteraction:
    def __init__(self):
        self.atag = AtagDataStore(
            host=settings.atag_host,
            hostname=settings.hostname,
            paired=True)

    def main(self):
        self.eventloop = None
        try:
            self.eventloop = asyncio.get_event_loop()
            logger.info('Setup connection to ATAG ONE')
            self.eventloop.run_until_complete(self.setup())
            logger.info('Starting the main loop for ATAG ONE')
            self.eventloop.create_task(self.loop())
            self.eventloop.run_forever()
        except KeyboardInterrupt:
            logger.info('Closing connection to ATAG ONE')
        finally:
            logger.info('Cleaning up')
            if self.eventloop:
                self.eventloop.run_until_complete(self.eventloop.shutdown_asyncgens())
                self.eventloop.close()
                self.eventloop = None


    async def setup(self):
        if settings.atag_host:
            logger.info(f"Using configured ATAG ONE {settings.atag_host}")
        else:
            logger.info(f"Discovering ATAG ONE")
            await self.atag.async_host_search()
        
        await self.atag.async_update()
        self.device = Device_AtagOne(self.atag,name="Atag One",eventloop=self.eventloop)
        logger.info(f"Connected to ATAG_ONE device {self.atag.device} @ {self.atag.config.host}")

    async def loop(self):
        next_time = self.eventloop.time()
        while True:
            await asyncio.sleep(1)
            if (self.eventloop.time() > next_time):
                await self.device.update()
                logger.info('Updated at: {}'.format(self.atag.sensordata['date_time']['state']))
                next_time = self.eventloop.time() + settings.atag_update_interval

