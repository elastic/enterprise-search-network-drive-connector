#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run a full sync against a Network Drives.

    It will attempt to sync absolutely all documents that are available in the
    third-party system and ingest them into Enterprise Search instance.
"""
from multiprocessing import Process

from .connector_queue import ConnectorQueue
from .base_command import BaseCommand
from .checkpointing import Checkpoint
from .sync_network_drives import init_network_drives_sync
from .sync_enterprise_search import init_enterprise_search_sync
from .utils import get_current_time

INDEXING_TYPE = "full"


class FullSyncCommand(BaseCommand):
    """This class start executions of fullsync feature."""

    def execute(self):
        """This function execute the start function."""
        config = self.config
        logger = self.logger
        workplace_search_client = self.workplace_search_client
        network_drive_client = self.network_drive_client
        indexing_rules = self.indexing_rules
        storage_obj = self.local_storage
        current_time = get_current_time()
        checkpoint = Checkpoint(config, logger)
        drive = config.get_value("network_drive.server_name")

        time_range = {
            "start_time": config.get_value("start_time"),
            "end_time": current_time,
        }
        logger.info(f"Indexing started at: {current_time}")

        queue = ConnectorQueue()
        producer = Process(
            name="producer",
            target=init_network_drives_sync,
            args=(
                time_range,
                config,
                logger,
                workplace_search_client,
                network_drive_client,
                indexing_rules,
                storage_obj,
                queue,
            ),
        )
        producer.start()
        consumer = Process(
            name="consumer_process",
            target=init_enterprise_search_sync,
            args=(config, logger, workplace_search_client, queue),
        )

        consumer.start()

        producer.join()
        consumer.join()
        checkpoint.set_checkpoint(current_time, INDEXING_TYPE, drive)
        logger.info(f"Indexing ended at: {get_current_time()}")
