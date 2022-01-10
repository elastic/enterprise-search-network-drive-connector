# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import time
from pathlib import Path
from tika.tika import TikaException
from src.utils import hash_id, extract
import os
from dateutil.parser import parse
import src.adapter as adapter
from src.indexing_rule import IndexingRules
import tempfile
from src.base_class import BaseClass
from src.constant import DATETIME_FORMAT


class Files:
    def __init__(self, logger):
        self.logger = logger
        BaseClass.__init__(self, logger=self.logger)

    def recursive_fetch(self, conn, service_name, path, store, time_range):
        """This method is used to recursively fetch files from network Drive.
            :param conn: SMB connection object
            :param service_name: name of the drive
            :param path: Path of the network drive
            :param store: temporary storage for fetched ids from Drive
            :param time_range: Start and End Time of process in multiprocessing
            :returns: dictionary of ids and file details for the files fetched
        """
        try:
            n_files = conn.listPath(service_name, rf'{path}')
        except Exception as exception:
            self.logger.exception("Unknown Error while fetching files %s" % (exception))
            return store
        for file_n in n_files:
            if file_n.filename not in ['.', '..']:
                file_name = file_n.filename
                if file_n.isDirectory:
                    self.recursive_fetch(conn, service_name, os.path.join(path, file_name), store, time_range)
                else:
                    updation_time = time.strftime(DATETIME_FORMAT, time.gmtime(file_n.last_attr_change_time))
                    file_details = {'updation_time': updation_time, 'file_type': os.path.splitext(file_name)[1], 'file_size': file_n.file_size,
                                    'create_time': file_n.create_time, 'file_name': file_name, 'file_path': os.path.join(path, file_name)}
                    filterobj = IndexingRules()
                    filter_rules = filterobj.apply_rules(file_details, self.include, self.exclude)
                    if filter_rules and parse(time_range.get('start_time')) < parse(updation_time) < parse(time_range.get('end_time')):
                        file_id = file_n.file_id if file_n.file_id else hash_id(file_name, path)
                        store.update({file_id: file_details})
        return store

    def fetch_files(self, connection, time_range):
        """This method is used to fetch and index files to Workplace Search
            :param connection: SMB connection object to the drive
            :param time_range: Start and End Time of process in multiprocessing
            :returns: list of documents fetched from the drive
        """
        schema = adapter.FILES
        document = []
        drive_path = Path(self.drive_path)
        store = self.recursive_fetch(
            connection, drive_path.parts[0], os.path.join(*drive_path.parts[1:]), {}, time_range)
        self.logger.info(
            "Successfuly fetched and parsed files from the Network Drive")
        for file_id, file_details in store.items():
            doc = {}
            file_obj = tempfile.NamedTemporaryFile()
            for field, file_field in schema.items():
                doc[field] = file_details.get(file_field)
            doc['id'] = str(file_id)
            doc['body'] = {}
            try:
                connection.retrieveFile(drive_path.parts[0], file_details.get('file_path'), file_obj)
                file_obj.seek(0)
                try:
                    doc['body'] = extract(file_obj.read())
                except TikaException as exception:
                    self.logger.exception(
                        "Error while extracting contents from file via Tika Parser. Error %s" % (exception))
            except Exception as exception:
                self.logger.exception(
                    "Cannot read the contents of the file. Error %s" % (exception))
            document.append(doc)
        return document
