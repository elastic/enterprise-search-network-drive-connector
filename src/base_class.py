# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

from src.configuration import Configuration


class BaseClass(object):
    """ This is the base class for initializing most frequently used assets.
    """
    def __init__(self, **kwargs):
        config = Configuration(kwargs.get("logger"))
        self.configurations = config.configurations
        self.retry_count = int(self.configurations.get("retry_count"))
        self.domain = self.configurations.get("network_drive.domain")
        self.username = self.configurations.get("network_drive.username")
        self.password = self.configurations.get("network_drive.password")
        self.drive_path = self.configurations.get("network_drive.path")
        self.client_machine_name = self.configurations.get("client_machine.name")
        self.server_name = self.configurations.get("network_drive.server_name")
        self.server_ip = self.configurations.get("network_drive.server_ip")
        self.include = self.configurations.get("include")
        self.exclude = self.configurations.get("exclude")
        self.ws_host = self.configurations.get("enterprise_search.host_url")
        self.ws_token = self.configurations.get("enterprise_search.access_token")
        self.ws_source = self.configurations.get("enterprise_search.source_id")


if __name__ == "__main__":
    BaseClass()
