#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run an incremental sync against a Network Drive Server instance.

    It will attempt to sync documents that have changed or have been added in the
    third-party system recently and ingest them into Enterprise Search instance.

    Recency is determined by the time when the last successful incremental or full job
    was ran.
"""
from .base_command import BaseCommand
from .indexer import start


class IncrementalSyncCommand(BaseCommand):
    def execute(self):
        config = self.config
        logger = self.logger
        workplace_search_client = self.workplace_search_client
        network_drive_client = self.network_drive_client

        start("incremental", config, logger, workplace_search_client, network_drive_client)
