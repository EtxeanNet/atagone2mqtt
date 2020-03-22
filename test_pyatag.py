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

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


ATAG_CONFIGURATION = {
    'host': '192.168.249.10',
    'hostname': 'atagmqtt'
}

class Test:
    def __init__(self):
        self.atag = AtagDataStore(**ATAG_CONFIGURATION)


    async def setup(self):
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
        # await self.temperature_updown(1)

    async def loop(self):
        while True:
            await self.atag.async_update()
            LOGGER.info('Updated at: {}'.format(self.atag.sensordata['date_time']['state']))
            # print(self.atag.sensordata)
            await asyncio.sleep(15)

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

    async def main(self):
        """Start infinite polling loop"""
        task = asyncio.Task(self.loop())
        await asyncio.sleep(10)
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

if __name__ == "__main__":
    loop = None
    try:
        test = Test()
        loop = asyncio.get_event_loop()
        LOGGER.info('Setup connection to ATAG ONE')
        loop.run_until_complete(test.setup())
        LOGGER.info('Starting the main loop')
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

