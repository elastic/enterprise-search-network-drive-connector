#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to remove recently deleted documents from Elastic Enterprise Search.

    Documents that were deleted in Network Drive will still be available in
    Elastic Enterprise Search until a full sync happens, or until this module is used.
"""

import json
import os
from pathlib import Path

from .base_command import BaseCommand
from . import constant


class DeletionSyncCommand(BaseCommand):
    """DeletionSyncCommand class allows to remove instances of specific files.

    It provides a way to remove those files from Elastic Enterprise Search
    that were deleted in Network Drive Server instance."""

    def __init__(self, args):
        super().__init__(args)
        self.logger.info('Initializing the dendexing class')
        self.server_name = self.config.get_value("network_drive.server_name")

    def format_ids(self, file_details):
        """Process doc_id.json file and prepare dictonary which is used for deleting all files under one folder
            :param file_details: dictionary containing file id and file path
            Returns:
                file_structure: dictionary containing folder and list of files inside the folder
        """
        file_structure = {}
        if file_details:
            for file_id, file_path in file_details.items():
                file_path, file_name = os.path.split(file_path)
                if file_structure.get(file_path):
                    file_structure[file_path][file_name] = file_id
                else:
                    file_structure[file_path] = {file_name: file_id}
        return file_structure

    def check_file_in_network_drive(self, drive_name, folder_path, file_structure, doc, visited_folders, deleted_folders):
        """Checks that folder/file present in network drive or not
            :param drive_name: the relative path of the Network Drive
            :param folder_path: the relative path of the folder
            :param file_structure: dictionary containing folder and list of files inside the folder
            :param doc: list of id's of deleted files
            :param visited_folders: list of visited path of folders
            :param deleted_folders: list of deleted path of folders
            Returns:
                folder_deleted: boolean value indicating folder is deleted or not
        """
        folder_deleted = False
        try:
            conn = self.network_drive_client.connect()
            if conn:
                drive_path = Path(self.config.get_value("network_drive.path"))
                available_files = conn.listPath(drive_path.parts[0], folder_path)
                for file_n in available_files:
                    if file_structure[folder_path].get(file_n.filename):
                        file_structure[folder_path].pop(file_n.filename)
                doc.extend(list(file_structure[folder_path].values()))
                visited_folders.append(folder_path)
                conn.close()
            else:
                self.logger.exception("Unknown error while connecting to network drive.")
        except Exception as exception:
            status = exception.smb_messages[-1].status
            if status in [constant.STATUS_NO_SUCH_FILE, constant.STATUS_NO_SUCH_DEVICE, constant.STATUS_OBJECT_NAME_NOT_FOUND]:
                for folder in file_structure.keys():
                    if folder_path in folder:
                        deleted_folders.append(folder)
                        self.logger.info(f"{folder} entire folder is deleted.")
                deleted_folders.append(folder_path)
                self.logger.info(f"{folder_path} entire folder is deleted.")
                return True
            elif status == constant.STATUS_OBJECT_PATH_NOT_FOUND:
                folder_path, file_name = os.path.split(folder_path)
                folder_deleted = self.check_file_in_network_drive(drive_name, folder_path, file_structure, doc,
                                                                  visited_folders, deleted_folders)
            else:
                self.logger.exception(f"Error while retrieving files from drive {drive_name}.Error: {exception}")
        return folder_deleted

    def deindexing_files(self, drive_name, ids):
        """Fetches the ids' of deleted files from the network drive and
            invokes delete documents api for those ids to remove them from
            workplace search
            :param drive_name: the relative path of the Network Drive
            :param ids: structure containing id's of all objects
            Returns:
                ids: updated structure containing id's of all objects after performing deindexing
        """
        file_details = ids["delete_keys"][drive_name].get("files")
        file_structure = self.format_ids(file_details)
        if file_details:
            doc = []
            deleted_folders = []
            visited_folders = []
            for file_id, file_path in file_details.items():
                folder_path, file_name = os.path.split(file_path)
                if folder_path in deleted_folders:
                    doc.append(file_id)
                    continue
                if folder_path in visited_folders:
                    continue
                folder_deleted = self.check_file_in_network_drive(drive_name, folder_path, file_structure,
                                                                  doc, visited_folders, deleted_folders)
                if folder_deleted:
                    doc.append(file_id)
            try:
                self.workplace_search_client.delete_documents(
                    content_source_id=self.config.get_value("enterprise_search.source_id"),
                    document_ids=doc)
                for id in doc:
                    ids["global_keys"][drive_name]["files"].pop(id)
            except Exception as exception:
                self.logger.exception(f"Error while de-indexing the files. Error: {exception}")
        else:
            self.logger.info(f"No files found to be deleted for drive: {drive_name}")
        return ids

    def execute(self):
        """Runs the de-indexing logic
        """

        self.logger.info('Starting the deletion sync..')

        try:
            with open(constant.IDS_PATH) as ids_file:
                ids = json.load(ids_file)
            self.logger.info(f'Starting the deindexing for drive: {self.server_name}')
            if ids["delete_keys"].get(self.server_name):
                ids = self.deindexing_files(self.server_name, ids)
            else:
                self.logger.info(f"No objects present to be deleted for the drive: {self.server_name}")
            ids["delete_keys"] = {}
            with open(constant.IDS_PATH, "w") as ids_file:
                try:
                    json.dump(ids, ids_file, indent=4)
                except ValueError as exception:
                    self.logger.exception(
                        f"Error while updating the doc_id json file. Error: {exception}"
                    )
        except FileNotFoundError as exception:
            self.logger.warning(
                f"[Fail] File doc_id.json is not present, none of the objects are indexed. Error: {exception}"
            )
