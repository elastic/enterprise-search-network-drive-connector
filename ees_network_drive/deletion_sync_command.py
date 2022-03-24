#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to remove recently deleted documents from Elastic Enterprise Search.

    Documents that were deleted in Network Drives will still be available in
    Elastic Enterprise Search until a full sync happens, or until this module is used.
"""
import os

from . import constant
from .base_command import BaseCommand
from .files import Files
from .utils import group_files_by_folder_path, split_documents_into_equal_chunks


class DeletionSyncCommand(BaseCommand):
    """DeletionSyncCommand class allows to remove instances of specific files.

    It provides a way to remove those files from Elastic Enterprise Search
    that were deleted in Network Drives Server instance."""

    def __init__(self, args):
        super().__init__(args)
        self.logger.debug("Initializing the deletion sync class")
        self.server_name = self.config.get_value("network_drive.server_name")

    def get_deleted_files(self, drive_name, ids):
        """Fetches the ids of deleted files from the Network Drives
        :param drive_name: service name of the Network Drives
        :param ids: structure containing id's of all files
        Returns:
            ids_list: list of file ids that got deleted from Network Drives
        """
        file_details = ids["delete_keys"][drive_name].get("files")
        file_structure = group_files_by_folder_path(file_details)
        ids_list = []
        if file_details:
            deleted_folders = []
            visited_folders = []
            smb_connection = self.network_drive_client.connect()
            if smb_connection:
                for file_id, file_path in file_details.items():
                    folder_path, file_name = os.path.split(file_path)
                    if folder_path in deleted_folders:
                        ids_list.append(file_id)
                        continue
                    if folder_path in visited_folders:
                        continue
                    files = Files(self.logger, self.config, self.network_drive_client)
                    folder_deleted = files.is_file_present_on_network_drive(
                        smb_connection,
                        drive_name,
                        folder_path,
                        file_structure,
                        ids_list,
                        visited_folders,
                        deleted_folders,
                    )
                    if folder_deleted:
                        ids_list.append(file_id)
            else:
                raise ConnectionError(
                    "Unknown error while connecting to network drives"
                )
        else:
            self.logger.info(f"No files found to be deleted for drive: {drive_name}")
        return ids_list

    def sync_deleted_files(self, ids_list, ids):
        """Invokes delete documents api for the deleted files ids to remove them from
        workplace search.
        :param ids_list: list of ids of files to be deleted from Enterprise Search
        :param ids: structure containing ids of all files
        Returns:
            ids: updated structure containing ids of all files after performing deletion
        """
        if ids_list:
            try:
                for chunk in split_documents_into_equal_chunks(
                    ids_list, constant.BATCH_SIZE
                ):
                    self.workplace_search_client.delete_documents(
                        content_source_id=self.config.get_value(
                            "enterprise_search.source_id"
                        ),
                        document_ids=chunk,
                    )
                for id in ids_list:
                    ids["global_keys"][self.server_name]["files"].pop(id)
            except Exception as exception:
                self.logger.exception(
                    f"Error while checking for deleted files. Error: {exception}"
                )
        return ids

    def execute(self):
        """Runs the deletion sync logic"""

        self.logger.info("Starting the deletion sync..")

        ids = self.local_storage.load_storage()
        self.logger.info(f"Starting the deletion sync for drive: {self.server_name}")
        if ids["delete_keys"].get(self.server_name):
            deleted_ids = self.get_deleted_files(self.server_name, ids)
            ids = self.sync_deleted_files(deleted_ids, ids)
        else:
            self.logger.debug(
                f"No objects present to be deleted for the drive: {self.server_name}"
            )
        ids["delete_keys"] = {}
        self.local_storage.update_storage(ids)
