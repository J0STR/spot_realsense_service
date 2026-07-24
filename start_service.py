import logging

from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                 DirectoryRegistrationKeepAlive)
from bosdyn.client.util import setup_logging
import bosdyn.util

DIRECTORY_NAME = 'realsense-service'
AUTHORITY = 'robot-realsense-cam'
SERVICE_TYPE = 'bosdyn.api.ImageService'

_LOGGER = logging.getLogger(__name__)

from src.helper import *


if __name__ == '__main__':
    payload_ip = '192.168.50.5'
    port = 21012

    setup_logging(verbose=False, include_dedup_filter=True)
    sdk = bosdyn.client.create_standard_sdk("ImageServiceSDK")
    robot = sdk.create_robot('192.168.50.3')

    guid, secret = None, None
    with open('/opt/payload_credentials/payload_guid_and_secret', 'r') as f:
        lines = f.read().splitlines()
        
        if len(lines) >= 2:
            # Standard Spot CORE I/O format: GUID on line 1, SECRET on line 2
            guid = lines[0].strip()
            secret = lines[1].strip()
        elif len(lines) == 1:
            # Fallback if there are no newlines: split by the 36-character UUID length
            raw_string = lines[0].strip()
            guid = raw_string[:36]
            secret = raw_string[36:]

    robot.authenticate_from_payload_credentials(guid, secret)
    service_runner = run_service(robot, port, DIRECTORY_NAME,logger=_LOGGER)

    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, payload_ip, service_runner.port)

    with keep_alive:
        service_runner.run_until_interrupt()
