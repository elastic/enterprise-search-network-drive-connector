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