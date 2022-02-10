#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to sync data to Elastic Enterprise Search.
    It's possible to run full syncs and incremental syncs with this module.
"""
import copy
import json
import multiprocessing
import os
from datetime import datetime

from .checkpointing import Checkpoint
from .constant import DATETIME_FORMAT, DOCUMENT_SIZE, IDS_PATH
from .files import Files


class Indexer:
    """This class contains common logic for indexing to workplace search
    """

    def __init__(self, start_time, end_time, checkpoint, workplace_search_client, network_drive_client, config, logger):
        self.logger = logger
        self.config = config
        self.is_error = False
        self.start_time = start_time
        self.end_time = end_time
        self.checkpoint = checkpoint
        self.workplace_search_client = workplace_search_client
        self.network_drive_client = network_drive_client

    def index_document(self, document):
        """ This method indexes the documents to the workplace.
            :param document: list of documents to be indexed
        """
        try:
            if document:
                total_documents_indexed = 0
                document_list = [document[i * DOCUMENT_SIZE:(i + 1) * DOCUMENT_SIZE] for i in range((len(document) + DOCUMENT_SIZE - 1) // DOCUMENT_SIZE)]
                for chunk in document_list:
                    response = self.workplace_search_client.index_documents(
                        content_source_id=self.config.get_value("enterprise_search.source_id"),
                        documents=chunk
                    )
                    for each in response['results']:
                        if not each['errors']:
                            total_documents_indexed += 1
                        else:
                            self.logger.error("Unable to index the document with id: %s Error %s" % (each['id'], each['errors']))
                self.logger.info("Successfully indexed %s to the workplace out of %s" % (
                    total_documents_indexed, len(response['results'])))
        except Exception as exception:
            self.logger.exception("Error while indexing the files. Error: %s"
                                  % (exception)
                                  )
            self.is_error = True

    def indexing(self, drive, ids, storage, is_error_shared):
        """This method fetches all the objects from Network Drive server and
            ingests them into the workplace search
            :param drive: drive name
            :param ids: id drive of the all the objects
            :param storage: temporary storage for storing all the documents
            :param is_error_shared: list of all the is_error values
        """
        time_range = {'start_time': self.start_time, 'end_time': self.end_time}
        connection = self.network_drive_client.connect()
        if connection:
            files = Files(self.logger, self.config)
            document = files.fetch_files(connection, time_range)
            for doc in document:
                ids["files"].update({doc["id"]: doc['path']})
            self.index_document(document)
            self.logger.info(
                "Completed fetching all the objects for drive: %s"
                % (drive)
            )
            connection.close()
            prev_ids = storage["files"]
            prev_ids.update(ids["files"])
            storage["files"] = prev_ids
        else:
            self.is_error = True
        is_error_shared.append(self.is_error)


def datetime_partitioning(start_time, end_time, processes):
    """ Divides the timerange in equal partitions by number of processors
        :param start_time: start time of the interval
        :param end_time: end time of the interval
        :param processes: number of processors the device have
    """
    start_time = datetime.strptime(start_time, DATETIME_FORMAT)
    end_time = datetime.strptime(end_time, DATETIME_FORMAT)

    diff = (end_time - start_time) / processes
    for idx in range(processes):
        yield (start_time + diff * idx)
    yield end_time


def init_multiprocessing(start_time, end_time, drive, ids, storage, is_error_shared, checkpoint, workplace_search_client, network_drive_client, config, logger):
    """This method initializes the IndexUpdate class and kicks-off the multiprocessing. This is a wrapper method added to fix the pickling issue while using multiprocessing in Windows
            :param start_time: start time of the indexing
            :param end_time: end time of the indexing
            :param drive: drive name
            :param ids: id drive of the all the objects
            :param storage: temporary storage for storing all the documents
            :param is_error_shared: list of all the is_error values
            :param checkpoint: checkpoint details
            :param workplace_search_client: cached workplace_search client object
            :param network_drive_client: cached connection object to network drive
            :param config: configuration object
            :param logger: logger object
        """
    indexer = Indexer(start_time, end_time, checkpoint, workplace_search_client, network_drive_client, config, logger)
    indexer.indexing(drive, ids, storage, is_error_shared)


def start(indexing_type, config, logger, workplace_search_client, network_drive_client):
    """Runs the indexing logic
        :param indexing_type: The type of the indexing i.e. Incremental Sync or Full sync
        :param config: configuration object
        :param logger: cached logger object
        :param workplace_search_client: cached workplace_search client object
        :param network_drive_client: cached connection object to network drive
    """
    logger.info("Starting the indexing..")
    is_error_shared = multiprocessing.Manager().list()
    current_time = (datetime.utcnow()).strftime(DATETIME_FORMAT)
    ids_collection = {"global_keys": {}}
    storage_with_collection = {"global_keys": {}, "delete_keys": {}}

    if (os.path.exists(IDS_PATH) and os.path.getsize(IDS_PATH) > 0):
        with open(IDS_PATH) as ids_store:
            try:
                ids_collection = json.load(ids_store)
            except ValueError as exception:
                logger.exception(
                    "Error while parsing the json file of the ids store from path: %s. Error: %s"
                    % (IDS_PATH, exception)
                )

    storage_with_collection["delete_keys"] = copy.deepcopy(ids_collection.get("global_keys"))

    drive = config.get_value("network_drive.server_name")
    storage = multiprocessing.Manager().dict({"files": {}})
    logger.info(
        "Starting the data fetching for drive: %s"
        % (drive)
    )
    check = Checkpoint(config, logger)

    worker_process = config.get_value("worker_process")
    if indexing_type == "incremental":
        start_time, end_time = check.get_checkpoint(
            current_time, drive)
    else:
        start_time = config.get_value("start_time")
        end_time = current_time

    # partitioning the drive timeframe in equal parts by worker processes
    partitions = list(datetime_partitioning(
        start_time, end_time, worker_process))

    datelist = []
    for sub in partitions:
        datelist.append(sub.strftime(DATETIME_FORMAT))

    jobs = []
    if not ids_collection["global_keys"].get(drive):
        ids_collection["global_keys"][drive] = {
            "files": {}}

    for num in range(0, worker_process):
        start_time_partition = datelist[num]
        end_time_partition = datelist[num + 1]
        logger.info(
            "Successfully fetched the checkpoint details: start_time: %s and end_time: %s, calling the indexing"
            % (start_time_partition, end_time_partition)
        )

        process = multiprocessing.Process(target=init_multiprocessing, args=(start_time_partition, end_time_partition, drive, ids_collection["global_keys"][drive], storage, is_error_shared, check, workplace_search_client, network_drive_client, config, logger))
        jobs.append(process)

    for job in jobs:
        job.start()
    for job in jobs:
        job.join()
    storage_with_collection["global_keys"][drive] = storage.copy()
    logger.info(
        "Saving the checkpoint for the drive: %s" % (drive)
    )
    if True in is_error_shared:
        check.set_checkpoint(start_time, indexing_type, drive)
    else:
        check.set_checkpoint(end_time, indexing_type, drive)

    with open(IDS_PATH, "w") as ids_file:
        try:
            json.dump(storage_with_collection, ids_file, indent=4)
        except ValueError as exception:
            logger.warning(
                'Error while adding ids to json file. Error: %s' % (exception))
