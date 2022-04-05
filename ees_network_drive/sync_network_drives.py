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
import threading
from pathlib import Path

from .files import Files


class SyncNetworkDrives:
    """This class contains common logic for fetching from Network Drives"""

    def __init__(
        self,
        logger,
        config,
        time_range,
        workplace_search_client,
        network_drive_client,
        indexing_rules,
        queue,
    ):
        self.logger = logger
        self.config = config
        self.time_range = time_range
        self.drive_path = Path(self.config.get_value("network_drive.path"))
        self.workplace_search_client = workplace_search_client
        self.network_drive_client = network_drive_client
        self.indexing_rules = indexing_rules
        self.network_drives_sync_thread_count = config.get_value("network_drives_sync_thread_count")
        self.queue = queue

    def get_storage_with_collection(self, local_storage):
        """Returns a dictionary containing the locally stored IDs of files fetched from network drives
        :param local_storage: The object of the local storage used to store the indexed document IDs
        """
        storage_with_collection = {"global_keys": {}, "delete_keys": {}}
        ids_collection = local_storage.load_storage()
        storage_with_collection["delete_keys"] = copy.deepcopy(ids_collection.get("global_keys"))

        if not ids_collection["global_keys"]:
            ids_collection["global_keys"] = {"files": {}}

        storage_with_collection["global_keys"] = copy.deepcopy(ids_collection["global_keys"])

        return storage_with_collection

    def connect_and_get_all_folders(self):
        """Connects to the Network drive and returns the list of all the folders present on the Network drive"""
        smb_connection = self.network_drive_client.connect()
        if not smb_connection:
            raise Exception("Unkown error while connecting to the Network Drives")
        store = []
        files = Files(self.logger, self.config, self.network_drive_client)
        store = files.recursive_fetch(
            smb_connection=smb_connection,
            service_name=self.drive_path.parts[0],
            path=os.path.join(*self.drive_path.parts[1:]),
            store=[],
        )
        smb_connection.close()
        return store

    def perform_sync(self, drive, partition_paths):
        """This method fetches all the objects from Network Drives server and
        appends them to the shared queue
        :param drive: The Network Drive name
        :param indexing_rules: Object of the indexing rules
        Returns:
            storage: dictionary containing the ids and path of all the files in Network Drives
        """
        if not partition_paths:
            return {}

        files = Files(self.logger, self.config, self.network_drive_client)
        documents_to_index = []
        self.logger.info(f"Thread: [{threading.get_ident()}] fetching all the files for folder {partition_paths}")
        ids_storage = {}
        try:
            fetched_documents = files.fetch_files(
                self.drive_path.parts[0],
                partition_paths,
                self.time_range,
                self.indexing_rules,
            )
            self.queue.append_to_queue(fetched_documents)
            documents_to_index.extend(fetched_documents)
        except Exception as exception:
            self.logger.error(f"Error while fetching files for the path: {partition_paths}. Error: {exception}")

        for doc in documents_to_index:
            ids_storage.update({doc["id"]: doc["path"]})

        return ids_storage
