# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import time
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from elastic_enterprise_search import WorkplaceSearch
from src.network_drive_client import NetworkDrive
from src.base_class import BaseClass
import src.logger_manager as log
from src.constant import IDS_PATH, STATUS_OBJECT_PATH_NOT_FOUND, STATUS_OBJECT_NAME_NOT_FOUND, STATUS_NO_SUCH_DEVICE, STATUS_NO_SUCH_FILE

logger = log.setup_logging('network_drive_connector_deindex')


class Deindex(BaseClass):
    def __init__(self):
        logger.info('Initializing the dendexing class')
        BaseClass.__init__(self, logger=logger)
        self.network_drive_client = NetworkDrive(logger)
        self.ws_client = WorkplaceSearch(self.ws_host, http_auth=self.ws_token)

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
                available_files = conn.listPath('Users', folder_path)
                for file_n in available_files:
                    if file_structure[folder_path].get(file_n.filename):
                        file_structure[folder_path].pop(file_n.filename)
                doc.extend(list(file_structure[folder_path].values()))
                visited_folders.append(folder_path)
                conn.close()
            else:
                logger.exception("Unknown error while connecting to network drive.")
        except Exception as exception:
            status = exception.smb_messages[-1].status
            if status in [STATUS_NO_SUCH_FILE, STATUS_NO_SUCH_DEVICE, STATUS_OBJECT_NAME_NOT_FOUND]:
                for folder in file_structure.keys():
                    if folder_path in folder:
                        deleted_folders.append(folder)
                        logger.info(f"{folder} entire folder is deleted.")
                deleted_folders.append(folder_path)
                logger.info(f"{folder_path} entire folder is deleted.")
                return True
            elif status == STATUS_OBJECT_PATH_NOT_FOUND:
                folder_path, file_name = os.path.split(folder_path)
                folder_deleted = self.check_file_in_network_drive(drive_name, folder_path, file_structure, doc,
                                                                  visited_folders, deleted_folders)
            else:
                logger.exception(f"Error while retrieving files from drive {drive_name}.Error: {exception}")
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
                self.ws_client.delete_documents(
                    content_source_id=self.ws_source,
                    document_ids=doc)
                for id in doc:
                    ids["global_keys"][drive_name]["files"].pop(id)
            except Exception as exception:
                logger.exception(f"Error while de-indexing the files. Error: {exception}")
        else:
            logger.info(f"No files found to be deleted for drive: {drive_name}")
        return ids


def start():
    """Runs the de-indexing logic regularly after a given interval
        or puts the connector to sleep
    """
    logger.info('Starting the de-indexing..')
    while True:
        deindexer = Deindex()
        try:
            with open(IDS_PATH) as f:
                ids = json.load(f)
            logger.info(f'Starting the deindexing for drive: {deindexer.server_name}')
            if ids["delete_keys"].get(deindexer.server_name):
                ids = deindexer.deindexing_files(deindexer.server_name, ids)
            else:
                logger.info(f"No objects present to be deleted for the drive: {deindexer.server_name}")
            ids["delete_keys"] = {}
            with open(IDS_PATH, "w") as f:
                try:
                    json.dump(ids, f, indent=4)
                except ValueError as exception:
                    logger.exception(
                        f"Error while updating the doc_id json file. Error: {exception}"
                    )
        except FileNotFoundError as exception:
            logger.warn(
                f"[Fail] File doc_id.json is not present, none of the objects are indexed. Error: {exception}"
            )
        deindexing_interval = deindexer.configurations.get('deletion_interval')
        logger.info('Sleeping..')
        time.sleep(deindexing_interval * 60)


if __name__ == "__main__":
    start()
