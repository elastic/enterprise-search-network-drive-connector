# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

class Deindexer:
    """ This class is responsible for deindexing documents from Enterprise Search if the document is removed from the Network Drive
    """

    def deindexing(self):
        """ This method fetches all the id's of deleted files and deletes them from Enterprise Search.
        """
        pass


def start():
    """ Runs the deindexing logic regularly after a given interval
        or puts the connector to sleep
    """
    pass
