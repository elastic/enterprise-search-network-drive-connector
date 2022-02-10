#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run a full sync against a Network Drive.

    It will attempt to sync absolutely all documents that are available in the
    third-party system and ingest them into Enterprise Search instance.
"""
from .base_command import BaseCommand
from .indexer import start


class FullSyncCommand(BaseCommand):
    def execute(self):
        config = self.config
        logger = self.logger
        workplace_search_client = self.workplace_search_client
        network_drive_client = self.network_drive_client

        start("full", config, logger, workplace_search_client, network_drive_client)
