#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""network_drive_client allows to call Network Drive and returns a connection object
    that can be used to fetch files from Network Drive.
"""
import time

from smb.base import NotConnectedError, SMBTimeout
from smb.SMBConnection import SMBConnection
from .constant import IS_DIRECT_TCP, SERVER_PORT, USE_NTLM_V2


class NetworkDrive:
    """Creates an SMB connection object to the Network Drive and returns the object
    """
    def __init__(self, config, logger):
        self.logger = logger
        self.client_machine_name = config.get_value("client_machine.name")
        self.server_name = config.get_value("network_drive.server_name")
        self.server_ip = config.get_value("network_drive.server_ip")
        self.domain = config.get_value("network_drive.domain")
        self.username = config.get_value("network_drive.username")
        self.password = config.get_value("network_drive.password")
        self.retry_count = int(config.get_value("retry_count"))

    def connect(self):
        """This method is used to connect with network drive.
        """
        conn = SMBConnection(self.username, self.password, self.client_machine_name, self.server_name, self.domain,
                             use_ntlm_v2=USE_NTLM_V2, is_direct_tcp=IS_DIRECT_TCP)
        retry = 0
        while retry <= self.retry_count:
            message = ""
            try:
                response = conn.connect(self.server_ip, SERVER_PORT)
                if response:
                    return conn
            except NotConnectedError as exception:
                message = "SMB connection has been disconnected or not connected yet"
                self.logger.exception("Error %s while connecting to network drive. Retry Count: %s. Error: %s"
                                      % (message, retry, exception)
                                      )
                # This condition is to avoid sleeping for the last time
                if retry < self.retry_count:
                    time.sleep(2 ** retry)
                retry += 1
            except SMBTimeout as exception:
                message = "SMBTimeout while waiting for the response for SMB/CIFS operation to complete"
                self.logger.exception(
                    "Error %s while connecting to network drive. Retry Count: %s. Error: %s"
                    % (message, retry, exception)
                )
                # This condition is to avoid sleeping for the last time
                if retry < self.retry_count:
                    time.sleep(2 ** retry)
                retry += 1
            except Exception as exception:
                self.logger.exception(
                    "Unkown Error while connecting to network drive. Error: %s"
                    % (exception)
                )
                break
