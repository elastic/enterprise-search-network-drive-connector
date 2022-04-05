#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import multiprocessing
from multiprocessing.queues import Queue
import threading


class ConnectorQueue(Queue):
    """Class to support additional queue operations specific to the connector"""

    def __init__(self, logger):
        ctx = multiprocessing.get_context()
        self.logger = logger
        super(ConnectorQueue, self).__init__(ctx=ctx)

    def end_signal(self):
        """Send an terminate signal to indicate the queue can be closed"""

        signal_close = {"type": "signal_close"}
        self.put(signal_close)

    def append_to_queue(self, documents):
        """Append documents to the shared queue
        :param documents: documents fetched from sharepoint
        """
        if documents:
            documents_map = {"type": "document_list", "data": documents}
            self.logger.debug(f"Thread ID {threading.get_ident()} added list of {len(documents)} \
                documents into the queue ")
            self.put(documents_map)
