#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Module responsible for fetching the files from the Network Drives and returning a document with
    all file details in json format.
"""
import errno
import os
import tempfile
import time
from pathlib import Path

from dateutil.parser import parse
from tika.tika import TikaException

from . import adapter, constant
from .utils import extract, fetch_users_from_csv_file, hash_id

ACCESS_ALLOWED_TYPE = 0
ACCESS_DENIED_TYPE = 1
ACCESS_MASK_DENIED_WRITE_PERMISSION = 278
ACCESS_MASK_ALLOWED_WRITE_PERMISSION = 1048854
STATUS_NO_SUCH_FILE = 3221225487
STATUS_NO_SUCH_DEVICE = 3221225486
STATUS_OBJECT_NAME_NOT_FOUND = 3221225524
STATUS_OBJECT_PATH_NOT_FOUND = 3221225530


class Files:
    """This class fetches objects from Network Drives
    """

    def __init__(self, logger, config, client):
        self.logger = logger
        self.user_mapping = config.get_value("network_drive_enterprise_search.user_mapping")
        self.drive_path = config.get_value("network_drive.path")
        self.server_ip = config.get_value("network_drive.server_ip")
        self.enable_document_permission = config.get_value("enable_document_permission")
        self.network_drives_client = client

    def recursive_fetch(self, smb_connection, service_name, path, store):
        """This method is used to recursively fetch folder paths from Network Drives.
            :param smb_connection: SMB connection object
            :param service_name: name of the drive
            :param path: Path of the Network Drives
            :param store: temporary storage for fetched ids from Drive
            :returns: list of all the folder paths in network drives
        """
        try:
            file_list = smb_connection.listPath(service_name, rf'{path}', search=16)
        except Exception as exception:
            self.logger.exception(f"Unknown error while fetching files {exception}")
            return store
        for file in file_list:
            if file.filename not in ['.', '..']:
                file_name = file.filename
                self.recursive_fetch(smb_connection, service_name, os.path.join(path, file_name), store)
        store.append(path)
        return store

    def extract_files(self, smb_connection, service_name, path, time_range, indexing_rules):
        """
            :param smb_connection: SMB connection object
            :param service_name: name of the drive
            :param path: Path of the Network Drives
            :param time_range: Start and End Time
            :param indexing_rules: object of indexing_rules
            :returns: dictionary of ids and file details for the files fetched
        """
        storage = {}
        try:
            file_list = smb_connection.listPath(service_name, rf'{path}')
        except Exception as exception:
            self.logger.exception(f"Unknown error while extracting files from folder {path}.Error {exception}")
            return storage
        for file in file_list:
            if not file.isDirectory:
                file_name = file.filename
                updated_at = \
                    time.strftime(constant.RFC_3339_DATETIME_FORMAT, time.gmtime(file.last_attr_change_time))
                created_at = \
                    time.strftime(constant.RFC_3339_DATETIME_FORMAT, time.gmtime(file.create_time))
                file_path = os.path.join(path, file_name)
                file_details = {
                    'updated_at': updated_at,
                    'file_type': os.path.splitext(file_name)[1],
                    'file_size': file.file_size,
                    'created_at': created_at,
                    'file_name': file_name,
                    'file_path': file_path,
                    'web_path': f"file://{self.server_ip}/{service_name}/{file_path}"
                }
                is_indexable = indexing_rules.should_index(file_details)
                if is_indexable \
                    and parse(time_range.get('start_time')) < parse(updated_at) \
                        and parse(updated_at) <= parse(time_range.get('end_time')):
                    file_id = file.file_id if file.file_id else hash_id(file_name, path)
                    storage.update({file_id: file_details})
        return storage

    def retrieve_permission(self, smb_connection, service_name, file_path):
        """This method is used to retrieve permission from Network Drives.
            :param smb_connection: SMB connection object
            :param service_name: name of the drive
            :param file_path: Path of the Network Drives
            :returns: hash of allow and deny permissions lists
        """
        try:
            security_info = smb_connection.getSecurity(service_name, rf'{file_path}')
        except Exception as exception:
            self.logger.exception(f"Unknown error while fetching permission details for file {file_path}.\
            Error {exception}")
            return [], []
        allow_users = []
        deny_users = []
        if security_info.dacl:
            aces = security_info.dacl.aces
            for ace in (aces or []):
                sid = str(ace.sid)
                if ace.type == ACCESS_ALLOWED_TYPE or ace.mask == ACCESS_MASK_DENIED_WRITE_PERMISSION:
                    allow_users.append(sid)
                if (ace.type == ACCESS_DENIED_TYPE and ace.mask != ACCESS_MASK_DENIED_WRITE_PERMISSION) or \
                        ace.mask == ACCESS_MASK_ALLOWED_WRITE_PERMISSION:
                    deny_users.append(sid)
                if not fetch_users_from_csv_file(self.user_mapping, self.logger).get(sid):
                    self.logger.warning(f"No mapping found for sid:{sid} in csv file. \
                        Please add the sid->user mapping for the {sid} and rerun the \
                        permission_sync_command to sync the user mappings.")
        return {'allow': allow_users, 'deny': deny_users}

    def fetch_files(self, service_name, path_list, time_range, indexing_rules):
        """This method is used to fetch and index files to Workplace Search
            :param service_name: name of the drive
            :param path_list: list of folder paths inside the network drives
            :param time_range: Start and End Time
            :param indexing_rules: object of indexing_rules
        """
        schema = adapter.FILES
        documents = []
        smb_connection = self.network_drives_client.connect()
        if smb_connection:
            for folder_path in path_list:
                storage = self.extract_files(smb_connection, service_name, folder_path, time_range, indexing_rules)
                for file_id, file_details in storage.items():
                    doc = {}
                    for field, file_field in schema.items():
                        doc[field] = file_details.get(file_field)
                    doc.update({'body': {}, 'id': str(file_id)})
                    if self.enable_document_permission:
                        permissions = self.retrieve_permission(
                            smb_connection, service_name, file_details.get("file_path"))
                        doc['_allow_permissions'] = permissions['allow']
                        doc['_deny_permissions'] = permissions['deny']
                    doc['body'] = self.fetch_file_content(service_name, file_details, smb_connection)
                    documents.append(doc)
            smb_connection.close()
        else:
            raise ConnectionError("Unknown error while connecting to network drives")
        return documents

    def is_file_present_on_network_drive(self, smb_connection, drive_name, folder_path,
                                         file_structure, ids_list, visited_folders, deleted_folders):
        """Checks that folder/file present in Network Drives or not
            :param smb_connection: connection object
            :param drive_name: service name of the Network Drives
            :param folder_path: the relative path of the folder
            :param file_structure: dictionary containing folder and list of files inside the folder
            :param ids_list: list of id's of deleted files
            :param visited_folders: list of visited path of folders
            :param deleted_folders: list of deleted path of folders
            Returns:
                folder_deleted: boolean value indicating folder is deleted or not
        """
        folder_deleted = False
        try:
            drive_path = Path(self.drive_path)
            available_files = smb_connection.listPath(drive_path.parts[0], folder_path)
            for file in available_files:
                if file_structure[folder_path].get(file.filename):
                    file_structure[folder_path].pop(file.filename)
            ids_list.extend(list(file_structure[folder_path].values()))
            visited_folders.append(folder_path)
        except Exception as exception:
            status = exception.smb_messages[-1].status
            if status in [STATUS_NO_SUCH_FILE, STATUS_NO_SUCH_DEVICE, STATUS_OBJECT_NAME_NOT_FOUND]:
                for folder in file_structure.keys():
                    if folder_path in folder:
                        deleted_folders.append(folder)
                        self.logger.info(f"{folder} entire folder is deleted.")
                deleted_folders.append(folder_path)
                return True
            elif status == STATUS_OBJECT_PATH_NOT_FOUND:
                folder_path, _ = os.path.split(folder_path)
                folder_deleted = self.is_file_present_on_network_drive(smb_connection, drive_name, folder_path,
                                                                       file_structure,
                                                                       ids_list, visited_folders, deleted_folders)
            else:
                self.logger.exception(f"Error while retrieving files from drive {drive_name}.Error: {exception}")
        return folder_deleted

    def fetch_file_content(self, service_name, file_details, smb_connection):
        """This method is used to fetch content from Network Drives file
        :param service_name: name of the drive
        :param file_details: dictionary containing file details
        :param smb_connection: connection object
        """
        file_obj = tempfile.NamedTemporaryFile()
        try:
            smb_connection.retrieveFile(service_name, file_details.get('file_path'), file_obj)
            file_obj.seek(0)
            try:
                extracted_content = extract(file_obj.read())
                file_obj.close()
                return extracted_content
            except TikaException as exception:
                self.logger.exception(
                    f"Error while extracting contents from file {file_details.get('file_name')} via Tika Parser. \
                        Error {exception}")
        except Exception as exception:
            if isinstance(exception, OSError) and exception.errno == errno.ENOSPC:
                self.logger.exception(
                    f"We reached the memory limit for extracting the file: {file_details.get('file_name')}. \
                        Skipping the contents of this file. Error: {exception}"
                )
            else:
                self.logger.exception(
                    f"Cannot read the contents of the file {file_details.get('file_name')} . Error {exception}")
        file_obj.close()