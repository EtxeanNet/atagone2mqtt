''' Interaction with ATAG ONE '''
import asyncio
import logging

from pyatag.gateway import AtagDataStore
from .device_atagone import DeviceAtagOne
from .configuration import Settings


SETTINGS = Settings()
LOGGER = logging.getLogger(__name__)

class AtagInteraction:
    ''' Interaction with ATAG as a datastore. '''
    def __init__(self):
        self.atag = AtagDataStore(host=SETTINGS.atag_host, hostname=SETTINGS.hostname, paired=True)
        self.eventloop = None
        self.device = None

    def main(self):
        ''' The main processing function. '''
        self.eventloop = None
        try:
            self.eventloop = asyncio.get_event_loop()
            LOGGER.info('Setup connection to ATAG ONE')
            self.eventloop.run_until_complete(self.setup())
            LOGGER.info('Starting the main loop for ATAG ONE')
            self.eventloop.create_task(self.loop())
            self.eventloop.run_forever()
        except KeyboardInterrupt:
            LOGGER.info('Closing connection to ATAG ONE')
        finally:
            LOGGER.info('Cleaning up')
            if self.eventloop:
                self.eventloop.run_until_complete(self.eventloop.shutdown_asyncgens())
                self.eventloop.close()
                self.eventloop = None

    async def setup(self):
        ''' Setup the connection with the ATAG ONE device. '''
        if SETTINGS.atag_host:
            LOGGER.info(f"Using configured ATAG ONE {SETTINGS.atag_host}")
        else:
            LOGGER.info(f"Discovering ATAG ONE")
            await self.atag.async_host_search()

        await self.atag.async_update()
        self.device = DeviceAtagOne(self.atag, name="Atag One", eventloop=self.eventloop)
        LOGGER.info(f"Connected to ATAG_ONE device {self.atag.device} @ {self.atag.config.host}")

    async def loop(self):
        ''' The event loop. '''
        next_time = self.eventloop.time()
        while True:
            await asyncio.sleep(1)
            if self.eventloop.time() > next_time:
                await self.device.update()
                LOGGER.info('Updated at: {}'.format(self.atag.sensordata['date_time']['state']))
                next_time = self.eventloop.time() + SETTINGS.atag_update_interval
