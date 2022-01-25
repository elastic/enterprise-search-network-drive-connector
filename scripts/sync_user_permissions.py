# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import time
from elastic_enterprise_search import WorkplaceSearch
import csv
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.logger_manager as log
from src.base_class import BaseClass


logger = log.setup_logging("network_drive_connector_index_permissions")


class SyncUserPermission:
    def __init__(self):
        logger.info("Initializing the Permission Indexing class")
        self.logger = logger
        self.is_error = False
        BaseClass.__init__(self, logger=logger)
        self.ws_client = WorkplaceSearch(self.ws_host, http_auth=self.ws_token)

    def remove_all_permissions(self):
        """ Removes all the permissions present in the workplace
        """
        try:
            user_permission = self.ws_client.list_permissions(
                content_source_id=self.ws_source,
            )

            if user_permission:
                self.logger.info("Removing the permissions from the workplace...")
                permission_list = user_permission['results']
                for permission in permission_list:
                    self.ws_client.remove_user_permissions(
                        content_source_id=self.ws_source,
                        user=permission['user'],
                        body={
                            "permissions": permission['permissions']
                        }
                    )
                self.logger.info("Successfully removed the permissions from the workplace.")
        except Exception as exception:
            self.logger.exception("Error while removing the permissions from the workplace. Error: %s" % exception)

    def workplace_add_permission(self, user_name, permissions):
        """This method when invoked would index the permission provided in the paramater
            for the user in paramter user_name
            :param permissions: list of permissions
            :param user_name: user to assign permissions
        """
        try:
            self.ws_client.add_user_permissions(
                content_source_id=self.ws_source,
                user=user_name,
                body={
                    "permissions": permissions
                },
            )
            self.logger.info(
                "Successfully indexed the permissions for user %s to the workplace" % (user_name)
            )
        except Exception as exception:
            self.logger.exception(
                "Error while indexing the permissions for user: %s to the workplace. Error: %s" % (user_name, exception)
            )

    def sync_permissions(self):
        """ This method when invoked, checks the permission of Network drive users and update those user
            permissions in the Workplace Search.
        """
        if (self.user_mapping and os.path.exists(self.user_mapping) and os.path.getsize(self.user_mapping) > 0):
            self.remove_all_permissions()
            mappings = {}
            with open(self.user_mapping) as file:
                try:
                    csvreader = csv.reader(file)
                    for row in csvreader:
                        if mappings.get(row[1]):
                            mappings[row[1]].append(row[0])
                        else:
                            mappings[row[1]] = [row[0]]
                except csv.Error as e:
                    self.logger.exception(f"Error while reading user mapping file at the location: {self.user_mapping}. Error: {e}")
            for key, val in mappings.items():
                self.workplace_add_permission(key, val)
        else:
            self.logger.error(f'Could not find the users mapping file at the location: {self.user_mapping} or the file is empty. Please add the sid->user mappings to sync the permissions in the Enterprise Search')
            exit(0)


def start():
    """ Runs the permission indexing logic regularly after a given interval
        or puts the connector to sleep
    """
    logger.info("Starting the permission indexing..")
    permission_indexer = SyncUserPermission()
    enable_permission = permission_indexer.enable_document_permission
    if not enable_permission:
        logger.error('Exiting as the enable permission flag is set to False')
        exit(0)
    sync_permission_interval = permission_indexer.configurations.get('sync_permission_interval')
    while True:
        permission_indexer.sync_permissions()
        logger.info('Sleeping..')
        time.sleep(sync_permission_interval * 60)


if __name__ == "__main__":
    start()
