#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run an incremental sync against a Network Drives Server instance.

    It will attempt to sync documents that have changed or have been added in the
    third-party system recently and ingest them into Enterprise Search instance.

    Recency is determined by the time when the last successful incremental or full job
    was ran.
"""
from .base_command import BaseCommand
from .checkpointing import Checkpoint
from .connector_queue import ConnectorQueue
from .local_storage import LocalStorage
from .sync_enterprise_search import SyncEnterpriseSearch
from .sync_network_drives import SyncNetworkDrives
from .utils import get_current_time, split_list_into_buckets

INDEXING_TYPE = "incremental"


class IncrementalSyncCommand(BaseCommand):
    """This class start executions of incrementalsync feature."""

    def start_producer(self, queue, time_range):
        """This method starts async calls for the producer which is responsible
        for fetching documents from the Network Drive and pushing them in the shared queue
        :param queue: Shared queue to store the fetched documents
        :param time_range: Time range dictionary storing start time and end time
        """
        logger = self.logger
        sync_network_drives = SyncNetworkDrives(
            logger,
            self.config,
            time_range,
            self.workplace_search_client,
            self.network_drive_client,
            self.indexing_rules,
            queue,
        )

        thread_count = self.config.get_value("network_drives_sync_thread_count")
        drive = self.config.get_value("network_drive.server_name")

        try:
            local_storage = LocalStorage(logger)
            storage_with_collection = sync_network_drives.get_storage_with_collection(local_storage)
            store = sync_network_drives.connect_and_get_all_folders()
            partition_paths = split_list_into_buckets(store, thread_count)

            global_keys = self.create_jobs(thread_count, sync_network_drives.perform_sync, (drive,), partition_paths)

            try:
                storage_with_collection["global_keys"]["files"].update(global_keys)
            except ValueError as value_error:
                logger.error(f"Exception while updating storage: {value_error}")

            # Send end signals for each live threads to notify them to close watching the queue
            # for any incoming documents
            for _ in range(self.config.get_value("enterprise_search_sync_thread_count")):
                queue.end_signal()
        except Exception as exception:
            logger.error("Error while Fetching from the Network drive. Checkpoint not saved")
            raise exception

        local_storage.update_storage(storage_with_collection)

    def start_consumer(self, queue):
        """This method starts async calls for the consumer which is responsible for indexing documents to the Enterprise Search
        :param queue: Shared queue to fetch the stored documents
        """
        logger = self.logger
        thread_count = self.config.get_value("enterprise_search_sync_thread_count")
        sync_es = SyncEnterpriseSearch(self.config, logger, self.workplace_search_client, queue)

        self.create_jobs(thread_count, sync_es.perform_sync, (), None)

    def execute(self):
        """This function execute the incremental sync."""
        config = self.config
        logger = self.logger
        current_time = get_current_time()
        checkpoint = Checkpoint(config, logger)
        drive = config.get_value("network_drive.server_name")

        start_time, end_time = checkpoint.get_checkpoint(current_time, drive)
        time_range = {"start_time": start_time, "end_time": end_time}
        logger.info(f"Indexing started at: {current_time}")

        queue = ConnectorQueue(logger)
        self.start_producer(queue, time_range)
        self.start_consumer(queue)
        checkpoint.set_checkpoint(current_time, INDEXING_TYPE, drive)
        logger.info(f"Indexing ended at: {get_current_time()}")
