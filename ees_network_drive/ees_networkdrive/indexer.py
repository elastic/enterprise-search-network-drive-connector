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
from pathlib import Path

from .utils import split_in_chunks
from multiprocessing.pool import ThreadPool

from .constant import BATCH_SIZE
from .files import Files


class Indexer:
    """This class contains common logic for indexing to workplace search
    """

    def __init__(self, logger, config, time_range, workplace_search_client, network_drive_client):
        self.logger = logger
        self.config = config
        self.time_range = time_range
        self.workplace_search_client = workplace_search_client
        self.network_drive_client = network_drive_client
        self.total_documents_indexed = 0
        self.max_threads = config.get_value("max_threads")

    def index_documents(self, documents):
        """ This method indexes the documents to the workplace.
            :param documents: list of documents to be indexed
        """
        try:
            if documents:
                for chunk in split_in_chunks(documents, BATCH_SIZE):
                    response = self.workplace_search_client.index_documents(
                        content_source_id=self.config.get_value("enterprise_search.source_id"),
                        documents=chunk
                    )
                    for each in response['results']:
                        if not each['errors']:
                            self.total_documents_indexed += 1
                        else:
                            self.logger.error(
                                f"Unable to index the document with id: {each['id']} Error {each['errors']}")
        except Exception as exception:
            self.logger.exception(f"Error while indexing the files. Error: {exception}"
                                  )
            raise exception

    def threaded_index_documents(self, documents):
        """This method multi threads the indexing of documents into Enterprise Search
            :param documents: documents to index to Enterprise Search
        """
        thread_pool = ThreadPool(self.max_threads)
        for document_list in self.partition_equal_share(documents, self.config.get_value("max_threads")):
            thread_pool.apply_async(self.index_documents, (document_list, ))
        thread_pool.close()
        thread_pool.join()

        self.logger.info(f"Successfully indexed {self.total_documents_indexed} to workplace out of {len(documents)}")

    def partition_equal_share(self, list_path, total_groups):
        """divides the list in groups of approximately equal sizes
            :param list_path: list of folder paths
            :param total_groups: number of groups to be formed
        """
        if list_path:
            groups = min(total_groups, len(list_path))
            group_list = []
            for i in range(groups):
                group_list.append(list_path[i::groups])
            return group_list
        else:
            return []

    def indexing(self, drive, ids, drive_path, indexing_rules):
        """This method fetches all the objects from Network Drives server and
            ingests them into the workplace search
            :param drive: drive name
            :param ids: temporary storage containing ids and path of the files from doc_id.json
            :param drive_path: path to network drives
            :param indexing_rules: object of indexing rules
        """
        connection = self.network_drive_client.connect()
        if connection:
            files = Files(self.logger, self.config, self.network_drive_client)
            store = files.recursive_fetch(conn=connection, service_name=drive_path.parts[0],
                                          path=os.path.join(*drive_path.parts[1:]), store=[])
            connection.close()
            partition_paths = self.partition_equal_share(store, self.max_threads)
            if partition_paths:
                documents = []
                documents_to_index = []
                thread_pool = ThreadPool(self.max_threads)
                for path_list in partition_paths:
                    thread = thread_pool.apply_async(files.fetch_files, (drive_path.parts[0],
                                                                         path_list, self.time_range, indexing_rules))
                    documents.append(thread)
                for result in [r.get() for r in documents]:
                    if result:
                        documents_to_index.extend(result)
                thread_pool.close()
                thread_pool.join()
                for doc in documents_to_index:
                    ids["files"].update({doc["id"]: doc['path']})
                self.threaded_index_documents(documents_to_index)
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
            self.logger.exception("Connection not established")
            raise ConnectionError


def start(time_range, config, logger, workplace_search_client, network_drive_client, indexing_rules, storage_obj):
    """Runs the indexing logic
        :param time_range: the duration considered for fetching files from network drives
        :param config: configuration object
        :param logger: cached logger object
        :param workplace_search_client: cached workplace_search client object
        :param network_drive_client: cached connection object to Network Drives
        :param indexing_rules: object of indexing rules
        :storage_obj: object for LocalStorage class used to fetch/update ids stored locally
    """
    logger.info("Starting the indexing..")
    ids_collection = {"global_keys": {}}
    storage_with_collection = {"global_keys": {}, "delete_keys": {}}

    try:
        ids_collection = storage_obj.load_storage()
    except FileNotFoundError:
        logger.debug("Local storage for ids was not found.")

    storage_with_collection["delete_keys"] = copy.deepcopy(ids_collection.get("global_keys"))

    drive = config.get_value("network_drive.server_name")
    logger.info(
        f"Starting the data fetching for drive: {drive}"
    )

    drive_path = config.get_value("network_drive.path")
    drive_path = Path(drive_path)

    try:
        if not ids_collection["global_keys"].get(drive):
            ids_collection["global_keys"][drive] = {
                "files": {}}
        indexer = Indexer(logger, config, time_range, workplace_search_client, network_drive_client)
        storage_with_collection["global_keys"][drive] = indexer.indexing(
            drive, ids_collection["global_keys"][drive], drive_path, indexing_rules)
        logger.info(
            f"Saving the checkpoint for the drive: {drive}"
        )

    except Exception as exception:
        logger.info("Error while indexing. Checkpoint not saved")
        raise exception

    storage_obj.update_storage(storage_with_collection)
