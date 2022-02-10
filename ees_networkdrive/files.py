#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Module responsible for fetching the files from the Network Drive and returning a document with
    all file details in json format.
"""
import csv
import os
import tempfile
import time
from pathlib import Path

from dateutil.parser import parse
from tika.tika import TikaException

from . import adapter, constant
from .indexing_rule import IndexingRules
from .utils import extract, hash_id


class Files:
    """This class fetches objects from network drive
    """
    def __init__(self, logger, config):
        self.logger = logger
        self.user_mapping = config.get_value("networkdrive_enterprisesearch.user_mapping")
        self.drive_path = config.get_value("network_drive.path")
        self.server_ip = config.get_value("network_drive.server_ip")
        self.include = config.get_value("include")
        self.exclude = config.get_value("exclude")
        self.enable_document_permission = config.get_value("enable_document_permission")
        self.sid_to_username = self.fetch_users_from_csv_file()

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
                    updation_time = time.strftime(constant.DATETIME_FORMAT, time.gmtime(file_n.last_attr_change_time))
                    creation_time = time.strftime(constant.DATETIME_FORMAT, time.gmtime(file_n.create_time))
                    file_path = os.path.join(path, file_name)
                    file_details = {'updation_time': updation_time, 'file_type': os.path.splitext(file_name)[1], 'file_size': file_n.file_size,
                                    'create_time': creation_time, 'file_name': file_name, 'file_path': file_path,
                                    'web_path': f"file://{self.server_ip}/{service_name}/{file_path}"}
                    filterobj = IndexingRules()
                    filter_rules = filterobj.apply_rules(file_details, self.include, self.exclude)
                    if filter_rules and parse(time_range.get('start_time')) < parse(updation_time) <= parse(time_range.get('end_time')):
                        file_id = file_n.file_id if file_n.file_id else hash_id(file_name, path)
                        store.update({file_id: file_details})
        return store

    def fetch_users_from_csv_file(self):
        """This method is used to map sid to username from csv file.
           :returns: dictionary of sid and username
        """
        rows = {}
        if (self.user_mapping and os.path.exists(self.user_mapping) and os.path.getsize(self.user_mapping) > 0):
            with open(self.user_mapping) as mapping_file:
                try:
                    csvreader = csv.reader(mapping_file)
                    for row in csvreader:
                        rows[row[0]] = row[1]
                except csv.Error as e:
                    self.logger.exception(f"Error while reading user mapping file at the location: {self.user_mapping}. Error: {e}")
        return rows

    def retrieve_permission(self, conn, service_name, path):
        """This method is used to retrieve permission from network drive.
            :param conn: SMB connection object
            :param service_name: name of the drive
            :param path: Path of the network drive
            :returns: list of allow and deny permissions
        """
        try:
            security_info = conn.getSecurity(service_name, rf'{path}')
        except Exception as exception:
            self.logger.exception("Unknown Error while fetching permission details for file %s. Error %s" % (path, exception))
            return [], []
        allow_users = []
        deny_users = []
        if security_info.dacl:
            aces = security_info.dacl.aces
            for ace in (aces or []):
                sid = str(ace.sid)
                if ace.type == constant.ACCESS_ALLOWED_TYPE or ace.mask == constant.ACCESS_MASK_DENIED_WRITE_PERMISSION:
                    allow_users.append(sid)
                if (ace.type == constant.ACCESS_DENIED_TYPE and ace.mask != constant.ACCESS_MASK_DENIED_WRITE_PERMISSION) or ace.mask == constant.ACCESS_MASK_ALLOWED_WRITE_PERMISSION:
                    deny_users.append(sid)
                if not self.sid_to_username.get(sid):
                    self.logger.warning(f"No mapping found for sid:{sid} in csv file. Please add the sid->user mapping for the {sid} and rerun the sync_user_permissions.py to sync the user mappings.")
        return allow_users, deny_users

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
            doc.update({'body': {}, 'id': str(file_id)})
            if self.enable_document_permission:
                allow_user_permission, deny_user_permission = self.retrieve_permission(connection, drive_path.parts[0],
                                                                                       file_details.get("file_path"))
                doc['_allow_permissions'] = allow_user_permission
                doc['_deny_permissions'] = deny_user_permission
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
