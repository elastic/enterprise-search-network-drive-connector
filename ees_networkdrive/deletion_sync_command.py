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

from .base_command import BaseCommand
from .files import Files
from .utils import split_in_chunks, group_files_by_folder_path
from . import constant


class DeletionSyncCommand(BaseCommand):
    """DeletionSyncCommand class allows to remove instances of specific files.

    It provides a way to remove those files from Elastic Enterprise Search
    that were deleted in Network Drives Server instance."""

    def __init__(self, args):
        super().__init__(args)
        self.logger.info('Initializing the deletion sync class')
        self.server_name = self.config.get_value("network_drive.server_name")

    def get_deleted_files(self, drive_name, ids):
        """Fetches the ids of deleted files from the Network Drives and
            invokes delete documents api for those ids to remove them from
            workplace search
            :param drive_name: service name of the Network Drives
            :param ids: structure containing id's of all objects
            Returns:
                ids: updated structure containing id's of all objects after performing deletion
        """
        file_details = ids["delete_keys"][drive_name].get("files")
        file_structure = group_files_by_folder_path(file_details)
        if file_details:
            ids_list = []
            deleted_folders = []
            visited_folders = []
            connection = self.network_drive_client.connect()
            if connection:
                for file_id, file_path in file_details.items():
                    folder_path, file_name = os.path.split(file_path)
                    if folder_path in deleted_folders:
                        ids_list.append(file_id)
                        continue
                    if folder_path in visited_folders:
                        continue
                    files = Files(self.logger, self.config, self.network_drive_client)
                    folder_deleted = files.check_file_in_network_drive(
                        connection, drive_name, folder_path, file_structure,
                        ids_list, visited_folders, deleted_folders
                    )
                    if folder_deleted:
                        ids_list.append(file_id)
                try:
                    for chunk in split_in_chunks(ids_list, constant.BATCH_SIZE):
                        self.workplace_search_client.delete_documents(
                            content_source_id=self.config.get_value("enterprise_search.source_id"),
                            document_ids=chunk)
                    for id in ids_list:
                        ids["global_keys"][drive_name]["files"].pop(id)
                except Exception as exception:
                    self.logger.exception(f"Error while checking for deleted files. Error: {exception}")
            else:
                self.logger.exception("Unknown error while connecting to network drives")
                raise ConnectionError
        else:
            self.logger.info(f"No files found to be deleted for drive: {drive_name}")
        return ids

    def execute(self):
        """Runs the deletion sync logic
        """

        self.logger.info('Starting the deletion sync..')

        try:
            ids = self.local_storage.load_storage()
            self.logger.info(f'Starting the deletion sync for drive: {self.server_name}')
            if ids["delete_keys"].get(self.server_name):
                ids = self.get_deleted_files(self.server_name, ids)
            else:
                self.logger.debug(f"No objects present to be deleted for the drive: {self.server_name}")
            ids["delete_keys"] = {}
            self.local_storage.update_storage(ids)
        except FileNotFoundError as exception:
            self.logger.warning(
                f"[Fail] File doc_id.json is not present, none of the objects are indexed. Error: {exception}"
            )
