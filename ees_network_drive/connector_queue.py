#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import multiprocessing
from multiprocessing.queues import Queue
from .utils import split_documents_into_equal_chunks
from .constant import BATCH_SIZE


class ConnectorQueue(Queue):
    """Class to support additional queue operations specific to the connector"""

    def __init__(self):
        ctx = multiprocessing.get_context()
        super(ConnectorQueue, self).__init__(ctx=ctx)

    def end_signal(self):
        """Send an terminate signal to indicate the queue can be closed"""

        signal_close = {"type": "signal_close"}
        self.put(signal_close)

    def put_checkpoint(self, key, checkpoint_time, indexing_type):
        """Put the checkpoint object in the queue which will be used by the consumer to update the checkpoint file

        :param key: The key of the checkpoint dictionary
        :param checkpoint_time: The end time that will be stored in the checkpoint as {'key': 'checkpoint_time'}
        :param indexing_type: The type of the indexing i.e. Full or Incremental
        """

        checkpoint = {
            "type": "checkpoint",
            "data": (key, checkpoint_time, indexing_type),
        }
        self.put(checkpoint)

    def append_to_queue(self, documents):
        """Append documents to the shared queue
        :param documents: documents fetched from sharepoint
        """
        if documents:
            for chunk in split_documents_into_equal_chunks(documents, BATCH_SIZE):
                document = {"type": "document_list", "data": chunk}
                self.put(document)
