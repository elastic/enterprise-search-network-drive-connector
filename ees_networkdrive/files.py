#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Module responsible for fetching the files from the Network Drives and returning a document with
    all file details in json format.
"""
import os
import tempfile
import time

from dateutil.parser import parse
from tika.tika import TikaException

from . import adapter, constant
from .utils import extract, hash_id, fetch_users_from_csv_file, multithreading

ACCESS_ALLOWED_TYPE = 0
ACCESS_DENIED_TYPE = 1
ACCESS_MASK_DENIED_WRITE_PERMISSION = 278
ACCESS_MASK_ALLOWED_WRITE_PERMISSION = 1048854


class Files:
    """This class fetches objects from Network Drives
    """
    def __init__(self, logger, config, client, indexing_rules):
        self.logger = logger
        self.user_mapping = config.get_value("network_drive_enterprise_search.user_mapping")
        self.drive_path = config.get_value("network_drive.path")
        self.server_ip = config.get_value("network_drive.server_ip")
        self.include = config.get_value("include")
        self.exclude = config.get_value("exclude")
        self.enable_document_permission = config.get_value("enable_document_permission")
        self.network_drives_client = client
        self.filterobj = indexing_rules

    def recursive_fetch(self, conn, service_name, path, store):
        """This method is used to recursively fetch folder paths from Network Drives.
            :param conn: SMB connection object
            :param service_name: name of the drive
            :param path: Path of the Network Drives
            :param store: temporary storage for fetched ids from Drive
            :returns: list of all the folder paths in network drives
        """
        try:
            file_list = conn.listPath(service_name, rf'{path}', search=16)
        except Exception as exception:
            self.logger.exception(f"Unknown Error while fetching files {exception}")
            return store
        for each_file in file_list:
            if each_file.filename not in ['.', '..']:
                file_name = each_file.filename
                self.recursive_fetch(conn, service_name, os.path.join(path, file_name), store)
        store.append(path)
        return store

    def extract_files(self, conn, service_name, path, time_range):
        """
            :param conn: SMB connection object
            :param service_name: name of the drive
            :param path: Path of the Network Drives
            :param time_range: Start and End Time
            :returns: dictionary of ids and file details for the files fetched
        """
        storage = {}
        try:
            file_list = conn.listPath(service_name, rf'{path}')
        except Exception as exception:
            self.logger.exception(f"Unknown Error while extracting files from folder {path}.Error {exception}")
            return storage
        for each_file in file_list:
            if not each_file.isDirectory:
                file_name = each_file.filename
                updated_at = time.strftime(constant.DATETIME_FORMAT, time.gmtime(each_file.last_attr_change_time))
                created_at = time.strftime(constant.DATETIME_FORMAT, time.gmtime(each_file.create_time))
                file_path = os.path.join(path, file_name)
                file_details = {'updated_time': updated_at, 'file_type': os.path.splitext(file_name)[1], 'file_size': each_file.file_size,
                                'created_at': created_at, 'file_name': file_name, 'file_path': file_path,
                                'web_path': f"file://{self.server_ip}/{service_name}/{file_path}"}
                is_indexable = self.filterobj.apply_rules(file_details, self.include, self.exclude)
                if is_indexable and parse(time_range.get('start_time')) < parse(updated_at) <= parse(time_range.get('end_time')):
                    file_id = each_file.file_id if each_file.file_id else hash_id(file_name, path)
                    storage.update({file_id: file_details})
        return storage

    def retrieve_permission(self, conn, service_name, path):
        """This method is used to retrieve permission from Network Drives.
            :param conn: SMB connection object
            :param service_name: name of the drive
            :param path: Path of the Network Drives
            :returns: tuple of allow and deny permissions lists
        """
        try:
            security_info = conn.getSecurity(service_name, rf'{path}')
        except Exception as exception:
            self.logger.exception(f"Unknown Error while fetching permission details for file {path}. Error {exception}")
            return [], []
        allow_users = []
        deny_users = []
        if security_info.dacl:
            aces = security_info.dacl.aces
            for ace in (aces or []):
                sid = str(ace.sid)
                if ace.type == ACCESS_ALLOWED_TYPE or ace.mask == ACCESS_MASK_DENIED_WRITE_PERMISSION:
                    allow_users.append(sid)
                if (ace.type == ACCESS_DENIED_TYPE and ace.mask != ACCESS_MASK_DENIED_WRITE_PERMISSION) or ace.mask == ACCESS_MASK_ALLOWED_WRITE_PERMISSION:
                    deny_users.append(sid)
                if not fetch_users_from_csv_file(self.user_mapping, self.logger).get(sid):
                    self.logger.warning(f"No mapping found for sid:{sid} in csv file. Please add the sid->user mapping for the {sid} and rerun the sync_user_permissions.py to sync the user mappings.")
        return allow_users, deny_users

    @multithreading
    def fetch_files(self, service_name, path_list, time_range, documents):
        """This method is used to fetch and index files to Workplace Search
            :param service_name: name of the drive
            :param path_list: list of folder paths inside the network drives
            :param time_range: Start and End Time
            :param documents: shared variable storing all the documents fetched
        """
        schema = adapter.FILES
        connection = self.network_drives_client.connect()
        if connection:
            for folder_path in path_list:
                storage = self.extract_files(connection, service_name, folder_path, time_range)
                for file_id, file_details in storage.items():
                    doc = {}
                    file_obj = tempfile.NamedTemporaryFile()
                    for field, file_field in schema.items():
                        doc[field] = file_details.get(file_field)
                    doc.update({'body': {}, 'id': str(file_id)})
                    if self.enable_document_permission:
                        allow_user_permission, deny_user_permission = self.retrieve_permission(connection, service_name,
                                                                                               file_details.get("file_path"))
                        doc['_allow_permissions'] = allow_user_permission
                        doc['_deny_permissions'] = deny_user_permission
                    try:
                        connection.retrieveFile(service_name, file_details.get('file_path'), file_obj)
                        file_obj.seek(0)
                        try:
                            doc['body'] = extract(file_obj.read())
                        except TikaException as exception:
                            self.logger.exception(
                                f"Error while extracting contents from file via Tika Parser. Error {exception}")
                    except Exception as exception:
                        self.logger.exception(
                            f"Cannot read the contents of the file. Error {exception}")
                    documents.append(doc)
            connection.close()
        else:
            self.logger.exception("Unknown error while connecting to network drives")
