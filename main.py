from pyatag.gateway import AtagDataStore
from pyatag import discovery
import async_timeout
# import homie
import aiohttp
import asyncio
import logging
from contextlib import suppress
import time
import sys
from atagmqtt.device_atagone import Device_AtagOne

from configuration import ATAG_CONFIGURATION

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class AtagInteraction:
    def __init__(self):
        self.atag = AtagDataStore(**ATAG_CONFIGURATION, paired=True)

    async def setup(self, eventloop):
        host = ATAG_CONFIGURATION.get('host',None)
        if host:
            LOGGER.info(f"Using configured ATAG ONE {host}")
            # self.atag = AtagDataStore(host=host, hostname="atagmqtt")
        else:
            LOGGER.info(f"Discovering ATAG ONE",hostname="atagmqtt")
            await self.atag.async_host_search()
        
        await self.atag.async_update()
        LOGGER.info(f"Connected to ATAG_ONE device={self.atag.device} @ {self.atag.config.host}")
        LOGGER.debug(self.atag.sensordata)
        self.device = Device_AtagOne(self.atag,name="Atag One",eventloop=eventloop)
        # await self.temperature_updown(1)

    async def loop(self):
        update_increment = ATAG_CONFIGURATION['update_interval']
        next_time = loop.time() + update_increment
        while True:
            if (loop.time() > next_time):
                await self.atag.async_update()
                self.device.update()
                LOGGER.info('Updated at: {}'.format(self.atag.sensordata['date_time']['state']))
                next_time = loop.time() + update_increment
            # print(self.atag.sensordata)
            await asyncio.sleep(1)

    async def temperature_updown(self, degrees: int, sleep: int = 10):
        old_temp = self.atag.sensordata['ch_mode_temp']['state']
        new_temp = old_temp + degrees
        LOGGER.info(f'Setting temperature to {new_temp}')
        success = await self.atag.set_temp(new_temp)
        if success:
            LOGGER.info(f'Temperature changed sucessfully to {new_temp}')
        else:
            LOGGER.warning('Could not change temperature')
        time.sleep(sleep)
        LOGGER.info(f'Setting temperature back to to {old_temp}')
        success = await self.atag.set_temp(old_temp)
        if success:
            LOGGER.info(f'Temperature set back to to {old_temp}') 
        else:
            LOGGER.warning('Could not set back temperature')

if __name__ == "__main__":
    loop = None
    try:
        test = AtagInteraction()
        loop = asyncio.get_event_loop()
        LOGGER.info('Setup connection to ATAG ONE')
        loop.run_until_complete(test.setup(loop))
        LOGGER.info('Starting the main loop for ATAG ONE')
        loop.create_task(test.loop())
        loop.run_forever()
    except KeyboardInterrupt:
        LOGGER.info('Closing connection to ATAG ONE')
    except:
        LOGGER.error(f"Unexpected error: {sys.exc_info()[1]}")
    finally:
        LOGGER.info('Cleaning up')
        if loop:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

