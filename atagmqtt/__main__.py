"""Interaction with ATAG ONE."""
import asyncio
import logging
import time
import aiohttp

from pyatag import AtagException, AtagOne
from pyatag.discovery import async_discover_atag
from .device_atagone import DeviceAtagOne
from .settings import Settings

_settings = Settings()
logging.basicConfig(level=_settings.loglevel, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logging.getLogger('pyatag').setLevel(_settings.loglevel)
logging.getLogger('homie').setLevel(_settings.loglevel)
logging.getLogger('homie.device_base').setLevel(logging.INFO)
logging.getLogger('homie.node').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

async def setup(settings: Settings, session: aiohttp.ClientSession, loop: asyncio.AbstractEventLoop) -> DeviceAtagOne:
    """Setup the connection with the ATAG ONE device."""
    if settings.atag_host:
        logger.info(f"Using configured AtagOne @ {settings.atag_host}")
    else:
        logger.info("Discovering AtagOne")
        atag_ip, _ = await async_discover_atag() # for auto discovery, requires access to UDP broadcast (hostnet)
        settings.atag_host = atag_ip
        logger.info(f"Using discovered AtagOne @ {settings.atag_host}")

    atag = AtagOne(settings.atag_host, session)
    logger.info("Authorizing...")
    await atag.authorize()
    logger.info("Updating...")
    await atag.update()
    logger.info("Creating Homie device...")
    device = DeviceAtagOne(atag, loop, "atagone", "Atag One", settings)
    logger.info(f"Setup connection from Homie device '{settings.homie_topic}/{device.device_id}'"
                f" to AtagOne @ {atag.host} succeeded")
    return device

async def main(settings):
    def handle_exception(loop, context):
        # context["message"] will always be there; but context["exception"] may not
        msg = context.get("exception", context["message"])
        logger.error(f"Caught exception: {msg}")

    logger.info("AtagOne2mqtt bridge is starting")
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)
    try:
        async with aiohttp.ClientSession() as session:
            logger.info('Setup connection to AtagOne')
            device = await asyncio.wait_for(setup(settings, session, loop), timeout=settings.atag_setup_timeout)
            logger.info('Start processing AtagOne reports and commands')
            while True:
                await asyncio.sleep(settings.atag_update_interval)
                await device.update()
                logger.info('Updated at: {}'.format(device.atag.report.report_time))
    except asyncio.TimeoutError:
        logger.error(f'Connection to AtagOne device could not be established within {settings.atag_setup_timeout} s')
    except AtagException as atag_ex:
        logger.error(f"Caught ATAG exception: {atag_ex}")
        logger.info(f'Waiting {_settings.restart_timeout} s to restart')
        time.sleep(_settings.restart_timeout)
    except KeyboardInterrupt:
        logger.info('Closing connection to AtagOne due to keyboard interrupt')
    finally:
        logger.info("AtagOne2mqtt bridge has stopped")

if __name__ == "__main__":
    asyncio.run(main(_settings))
