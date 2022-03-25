#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to sync data to Elastic Enterprise Search.
    It's possible to run full syncs and incremental syncs with this module.
"""
from multiprocessing.pool import ThreadPool

from .constant import BATCH_SIZE
from .utils import split_documents_into_equal_chunks


class SyncEnterpriseSearch:
    """This class contains common logic for indexing to workplace search"""

    def __init__(self, config, logger, workplace_search_client, queue):
        self.config = config
        self.logger = logger
        self.workplace_search_client = workplace_search_client
        self.queue = queue
        self.enterprise_search_sync_thread_count = config.get_value(
            "enterprise_search_sync_thread_count"
        )
        self.thread_pool = ThreadPool(self.enterprise_search_sync_thread_count)

    def index_documents(self, documents):
        """This method indexes the documents to the Enterprise Search.
        :param documents: list of documents to be indexed
        """
        try:
            if documents:
                total_documents_indexed = 0
                responses = self.workplace_search_client.index_documents(
                    content_source_id=self.config.get_value(
                        "enterprise_search.source_id"
                    ),
                    documents=documents,
                )
                for document in responses["results"]:
                    if not document["errors"]:
                        total_documents_indexed += 1
                    else:
                        self.logger.error(
                            f"Unable to index the document with id: {document['id']} Error {document['errors']}"
                        )
                self.logger.info(
                    f"Successfully indexed {total_documents_indexed} to the workplace out of {len(documents)}"
                )
        except Exception as exception:
            self.logger.exception(f"Error while indexing the files. Error: {exception}")
            raise exception

    def perform_sync(self):
        """Pull documents from the queue and index it to the Enterprise Search."""
        signal_open = True
        while signal_open:
            for _ in range(self.enterprise_search_sync_thread_count):
                documents_to_index = []
                while len(documents_to_index) < BATCH_SIZE:
                    documents = self.queue.get()
                    if documents.get("type") == "signal_close":
                        signal_open = False
                        break
                    else:
                        documents_to_index.extend(documents.get("data"))
                for document_list in split_documents_into_equal_chunks(
                    documents_to_index, BATCH_SIZE
                ):
                    self.thread_pool.apply_async(self.index_documents, (document_list,))
                if not signal_open:
                    break
        self.thread_pool.close()
        self.thread_pool.join()


def init_enterprise_search_sync(config, logger, workplace_search_client, queue):
    """Runs the indexing logic
    :param config: instance of Configuration class
    :param logger: instance of Logger class
    :param workplace_search_client: instance of WorkplaceSearch
    :param queue: Shared queue to push the objects fetched from Network Drives
    """
    indexer = SyncEnterpriseSearch(config, logger, workplace_search_client, queue)
    indexer.perform_sync()
