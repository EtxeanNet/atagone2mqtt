"""Interaction with ATAG ONE."""
import asyncio
import logging
import aiohttp

from pyatag import AtagException, AtagOne
from pyatag.discovery import discover_atag
from .device_atagone import DeviceAtagOne
from .settings import Settings

_settings = Settings()
logging.basicConfig(level=_settings.loglevel, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logging.getLogger('pyatag').setLevel(_settings.loglevel)
logging.getLogger('homie').setLevel(_settings.loglevel)
logging.getLogger('homie.device_base').setLevel(logging.INFO)
logging.getLogger('homie.node').setLevel(logging.INFO)
logger = logging.getLogger('atagmqtt')

async def main(settings: Settings):
    """Main function."""
    logger.info("Starting AtagOne2mqtt bridge")
    if settings.atag_host:
        logger.info(f"Using configured AtagOne @ {settings.atag_host}")
    else:
        logger.info("Discovering AtagOne")
        atag_ip, _ = discover_atag() # for auto discovery, requires access to UDP broadcast (hostnet)
        settings.atag_host = atag_ip
        logger.info(f"Using discovered AtagOne @ {settings.atag_host}")
    logger.info(f"Using MQTT broker @ {settings.mqtt_host}:{settings.mqtt_port}")

    while True:
        logger.info("AtagOne2mqtt bridge is starting")
        try:
            async with aiohttp.ClientSession() as session:
                logger.info('Setup connection to AtagOne')
                atag = AtagOne(settings.atag_host, session)
                logger.info("Authorizing...")
                await atag.authorize()
                logger.info("Updating...")
                await atag.update()
                logger.info("Creating Homie device...")
                device = DeviceAtagOne(atag, "atagone", "Atag One", settings)
                logger.info(f"Setup connection from Homie device '{settings.homie_topic}/{device.device_id}'"
                            f" to AtagOne @ {atag.host} succeeded")

                logger.info('Start processing AtagOne reports and commands')
                while True:
                    await asyncio.sleep(settings.atag_update_interval)
                    await device.update()
                    logger.info('Updated at: {}'.format(device.atag.report.report_time))

        except AtagException as atag_ex:
            logger.error(f"Caught ATAG exception: {atag_ex}")
            logger.info(f'Waiting {_settings.restart_timeout} s to restart')
            await asyncio.sleep(_settings.restart_timeout)
        except asyncio.CancelledError:
            logger.info('Closing connection to AtagOne due to cancellation')
            exit(0)
        except KeyboardInterrupt:
            logger.info('Closing connection to AtagOne due to keyboard interrupt')
            exit(0)
        except Exception as ex:
            logger.error(f"Caught unexected exception: {ex}")
            exit(1)
        finally:
            logger.info("AtagOne2mqtt bridge has stopped")

if __name__ == "__main__":
    asyncio.run(main(_settings))
