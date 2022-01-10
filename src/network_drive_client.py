# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import time
from smb.base import NotConnectedError, SMBTimeout
from src.base_class import BaseClass
from src.utils import print_and_log
from src.constant import USE_NTLM_V2, IS_DIRECT_TCP, SERVER_PORT
from smb.SMBConnection import SMBConnection


class NetworkDrive(BaseClass):
    def __init__(self, logger):
        self.logger = logger
        BaseClass.__init__(self, logger=logger)

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
                print_and_log(
                    self.logger,
                    "exception",
                    "Error %s while connecting to network drive. Retry Count: %s. Error: %s"
                    % (message, retry, exception)
                )
                # This condition is to avoid sleeping for the last time
                if retry < self.retry_count:
                    time.sleep(2 ** retry)
                retry += 1
            except SMBTimeout as exception:
                message = "SMBTimeout while waiting for the response for SMB/CIFS operation to complete"
                print_and_log(
                    self.logger,
                    "exception",
                    "Error %s while connecting to network drive. Retry Count: %s. Error: %s"
                    % (message, retry, exception)
                )
                # This condition is to avoid sleeping for the last time
                if retry < self.retry_count:
                    time.sleep(2 ** retry)
                retry += 1
            except Exception as exception:
                print_and_log(
                    self.logger,
                    "exception",
                    "Unkown Error while connecting to network drive. Error: %s"
                    % (exception)
                )
                break
