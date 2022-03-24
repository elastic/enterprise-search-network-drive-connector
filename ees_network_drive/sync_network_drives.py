#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to sync data to Elastic Enterprise Search.
    It's possible to run full syncs and incremental syncs with this module.
"""
import copy
import os
from multiprocessing.pool import ThreadPool
from pathlib import Path

from .files import Files
from .utils import split_list_into_buckets


class SyncNetworkDrives:
    """This class contains common logic for fetching from Network Drives"""

    def __init__(
        self,
        logger,
        config,
        time_range,
        workplace_search_client,
        network_drive_client,
        queue,
    ):
        self.logger = logger
        self.config = config
        self.time_range = time_range
        self.workplace_search_client = workplace_search_client
        self.network_drive_client = network_drive_client
        self.network_drives_sync_thread_count = config.get_value(
            "network_drives_sync_thread_count"
        )
        self.queue = queue
        self.thread_pool = ThreadPool(self.network_drives_sync_thread_count)

    def perform_sync(self, drive, ids, drive_path, indexing_rules):
        """This method fetches all the objects from Network Drives server and
        ingests them into the workplace search
        :param drive: drive name
        :param ids: temporary storage containing ids and path of the files from doc_id.json
        :param drive_path: path to network drives
        :param indexing_rules: object of indexing rules
        Returns:
            storage: dictionary containing the ids and path of all the files in Network Drives
        """
        smb_connection = self.network_drive_client.connect()
        if smb_connection:
            files = Files(self.logger, self.config, self.network_drive_client)
            store = files.recursive_fetch(
                smb_connection=smb_connection,
                service_name=drive_path.parts[0],
                path=os.path.join(*drive_path.parts[1:]),
                store=[],
            )
            smb_connection.close()
            partition_paths = split_list_into_buckets(
                store, self.network_drives_sync_thread_count
            )
            if partition_paths:
                documents = []
                documents_to_index = []
                for path_list in partition_paths:
                    thread = self.thread_pool.apply_async(
                        files.fetch_files,
                        (
                            drive_path.parts[0],
                            path_list,
                            self.time_range,
                            indexing_rules,
                        ),
                        callback=self.queue.append_to_queue,
                    )
                    documents.append(thread)
                for result in [r.get() for r in documents]:
                    if result:
                        documents_to_index.extend(result)
                self.thread_pool.close()
                self.thread_pool.join()
                for doc in documents_to_index:
                    ids["files"].update({doc["id"]: doc["path"]})
                self.logger.info(
                    f"Completed fetching all the objects for drive: {drive}"
                )
            else:
                self.logger.info("No files found in the network drives path")
            storage = {"files": {}}
            prev_ids = storage["files"]
            prev_ids.update(ids["files"])
            storage["files"] = prev_ids
            return storage
        else:
            raise ConnectionError("Connection not established")


def init_network_drives_sync(
    time_range,
    config,
    logger,
    workplace_search_client,
    network_drive_client,
    indexing_rules,
    storage_obj,
    queue,
):
    """Runs the fetching logic
    :param time_range: the duration considered for fetching files from network drives
    :param config: configuration object
    :param logger: cached logger object
    :param workplace_search_client: cached workplace_search client object
    :param network_drive_client: cached connection object to Network Drives
    :param indexing_rules: object of indexing rules
    :param storage_obj: object for LocalStorage class used to fetch/update ids stored locally
    :param queue: Shared queue to push the objects fetched from Network Drives
    """
    logger.info("Starting the indexing..")
    storage_with_collection = {"global_keys": {}, "delete_keys": {}}

    ids_collection = storage_obj.load_storage()

    storage_with_collection["delete_keys"] = copy.deepcopy(
        ids_collection.get("global_keys")
    )

    drive = config.get_value("network_drive.server_name")
    logger.info(f"Starting the data fetching for drive: {drive}")

    drive_path = config.get_value("network_drive.path")
    drive_path = Path(drive_path)

    try:
        if not ids_collection["global_keys"].get(drive):
            ids_collection["global_keys"][drive] = {"files": {}}
        sync_network_drives = SyncNetworkDrives(
            logger,
            config,
            time_range,
            workplace_search_client,
            network_drive_client,
            queue,
        )
        storage_with_collection["global_keys"][
            drive
        ] = sync_network_drives.perform_sync(
            drive, ids_collection["global_keys"][drive], drive_path, indexing_rules
        )
        queue.end_signal()
        logger.info(f"Saving the checkpoint for the drive: {drive}")

    except Exception as exception:
        logger.info("Error while indexing. Checkpoint not saved")
        raise exception

    storage_obj.update_storage(storage_with_collection)
