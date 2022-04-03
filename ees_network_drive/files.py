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
