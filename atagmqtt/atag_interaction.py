"""Interaction with ATAG ONE."""
import asyncio
import logging
import time
import aiohttp

from pyatag import AtagException, AtagOne
from pyatag.discovery import async_discover_atag
from .device_atagone import DeviceAtagOne
from .configuration import Settings

SETTINGS = Settings()
LOGGER = logging.getLogger(__name__)

async def main():
    """The main processing function."""
    async with aiohttp.ClientSession() as session:
        await run(session)

async def run(session: aiohttp.ClientSession):
    try:
        LOGGER.info('Setup connection to ATAG ONE')
        device = await setup(session)
        LOGGER.info('Starting the main loop for ATAG ONE')
        while True:
            await asyncio.sleep(SETTINGS.atag_update_interval)
            await device.update()
            LOGGER.info('Updated at: {}'.format(device.atag.report.report_time))
    except AtagException as atag_ex:
        LOGGER.error("ATAG execption: {atag_ex}")
        return False
    except KeyboardInterrupt:
        LOGGER.info('Closing connection to ATAG ONE')

async def setup(session: aiohttp.ClientSession) -> DeviceAtagOne:
    
    """Setup the connection with the ATAG ONE device."""
    if SETTINGS.atag_host:
        LOGGER.info(f"Using configured ATAG ONE {SETTINGS.atag_host}")
    else:
        LOGGER.info("Discovering ATAG ONE")
        atag_ip, _ = await async_discover_atag() # for auto discovery, requires access to UDP broadcast (hostnet)
        SETTINGS.atag_host = atag_ip

    timeout_task = asyncio.create_task(raise_timeout_after(10))
    atag = AtagOne(SETTINGS.atag_host, session)
    await atag.authorize()
    await atag.update(force=True)
    device = DeviceAtagOne(atag, asyncio.get_running_loop(), name="Atag One")
    timeout_task.cancel()
    LOGGER.info(f"Connected to ATAG ONE device @ {atag.host}")
    return device

async def raise_timeout_after(timeout: float):
    LOGGER.info(f"Timeout connection to ATAG ONE after {timeout} s")
    i = 0
    while i < timeout:
        i += 1
        LOGGER.info(f"Waiting another {timeout - i} s")
        await asyncio.sleep(1)

    raise TimeoutError("Connection to ATAG ONE device could not be established")
