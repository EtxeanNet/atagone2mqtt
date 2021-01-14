"""Interaction with ATAG ONE."""
import asyncio
import logging
import aiohttp

from pyatag import AtagException, AtagOne
from pyatag.discovery import async_discover_atag
from .device_atagone import DeviceAtagOne
from .configuration import Settings

SETTINGS = Settings()
LOGGER = logging.getLogger(__name__)

async def interact_with_atag(loop: asyncio.AbstractEventLoop, setup_timeout = 30):
    """The main processing function."""
    async with aiohttp.ClientSession() as session:
        LOGGER.info('Setup connection to ATAG ONE')
        device = await asyncio.wait_for(setup(session, loop), timeout=SETTINGS.atag_setup_timeout)
        LOGGER.info('Start processing ATAG ONE reports and commands')
        while True:
            await asyncio.sleep(SETTINGS.atag_update_interval)
            await device.update()
            LOGGER.info('Updated at: {}'.format(device.atag.report.report_time))

async def setup(session: aiohttp.ClientSession, loop: asyncio.AbstractEventLoop) -> DeviceAtagOne:

    """Setup the connection with the ATAG ONE device."""
    if SETTINGS.atag_host:
        LOGGER.info(f"Using configured ATAG ONE @ {SETTINGS.atag_host}")
    else:
        LOGGER.info("Discovering ATAG ONE")
        atag_ip, _ = await async_discover_atag() # for auto discovery, requires access to UDP broadcast (hostnet)
        SETTINGS.atag_host = atag_ip
        LOGGER.info(f"Using discovered ATAG ONE @ {SETTINGS.atag_host}")

    atag = AtagOne(SETTINGS.atag_host, session)
    LOGGER.info("Authorizing...")
    await atag.authorize()
    LOGGER.info("Updating...")
    await atag.update(force=True)
    LOGGER.info("Creating Homie device...")
    device = DeviceAtagOne(atag, loop)
    LOGGER.info(f"Setup connection from Homie device '{SETTINGS.homie_topic}/{device.device_id}'"
                f" to ATAG ONE @ {atag.host} succeeded")
    return device

def handle_exception(loop, context):
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])
    LOGGER.error(f"Caught exception: {msg}")

async def main():
    LOGGER.info("ATAG MQTT bridge is starting")
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)
    try:
        await interact_with_atag(loop)
    except asyncio.TimeoutError:
        LOGGER.error(f'Connection to ATAG ONE device could not be established within {SETTINGS.atag_setup_timeout} s')
    except AtagException as atag_ex:
        LOGGER.error(f"Caught ATAG exception: {atag_ex}")
    except KeyboardInterrupt:
        LOGGER.info('Closing connection to ATAG ONE due to keyboard interrupt')
    finally:
        LOGGER.info("ATAG MQTT bridge has stopped")
