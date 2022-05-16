#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to sync data to Elastic Enterprise Search.
    It's possible to run full syncs and incremental syncs with this module.
"""
import threading

from .constant import BATCH_SIZE, CONNECTION_TIMEOUT
from .utils import split_documents_into_equal_chunks


class SyncEnterpriseSearch:
    """This class contains common logic for indexing to workplace search"""

    def __init__(self, config, logger, workplace_search_custom_client, queue):
        self.logger = logger
        self.workplace_search_custom_client = workplace_search_custom_client
        self.queue = queue
        self.ws_source = config.get_value("enterprise_search.source_id")
        self.enterprise_search_sync_thread_count = config.get_value("enterprise_search_sync_thread_count")
        self.total_document_indexed = 0
        self.total_documents_found = 0

    def index_documents(self, documents):
        """This method indexes the documents to the Enterprise Search.
        :param documents: list of documents to be indexed
        """
        self.total_documents_found += len(documents)
        if documents:
            documents_indexed = 0
            responses = self.workplace_search_custom_client.index_documents(
                documents,
                CONNECTION_TIMEOUT,
            )
            for document in responses["results"]:
                if not document["errors"]:
                    documents_indexed += 1
                else:
                    self.logger.error(
                        f"Unable to index the document with id: {document['id']} Error {document['errors']}"
                    )
            self.total_document_indexed += documents_indexed

    def perform_sync(self):
        """Pull documents from the queue and synchronize it to the Enterprise Search."""
        try:
            signal_open = True
            while signal_open:
                documents_to_index = []
                while len(documents_to_index) < BATCH_SIZE:
                    document = self.queue.get()
                    if document.get("type") == "signal_close":
                        self.logger.info(f"Found an end signal in the queue. Closing Thread ID {threading.get_ident()}")
                        signal_open = False
                        break
                    else:
                        documents_to_index.extend(document.get("data"))
                # This loop is to ensure if the last document fetched from the queue exceeds the size of
                # documents_to_index to more than the permitted chunk size, then we split the documents as per the limit
                for document_list in split_documents_into_equal_chunks(documents_to_index, BATCH_SIZE):
                    self.index_documents(document_list)
        except Exception as exception:
            self.logger.error(exception)
        self.logger.info(f"Thread ID: {threading.get_ident()} Total {self.total_document_indexed} documents \
            indexed out of: {self.total_documents_found} till now..")
