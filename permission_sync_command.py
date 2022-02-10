#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run a deletion sync against a Network Drive instance.

    It will attempt to remove from Enterprise Search instance the documents
    that have been deleted from the third-party system.
"""
import csv
import os

from .base_command import BaseCommand


class PermissionSyncDisabledException(Exception):
    """Exception raised when permission sync is disabled, but expected to be enabled.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Provided configuration was invalid"):
        self.message = message
        super().__init__(message)


class EmptyMappingException(Exception):
    """Exception raised when mapping file is not present or empty and the sync_user_permissions
        is executed.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Mapping not found"):
        self.message = message
        super().__init__(message)


class PermissionSyncCommand(BaseCommand):
    """This class contains logic to sync user permissions from Network Drive Server.

    It can be used to run the job that will periodically sync permissions
    from Network Drive Server to Elastic Enteprise Search."""
    def __init__(self, args):
        super().__init__(args)

        config = self.config

        self.logger.info("Initializing the Permission Indexing class")
        self.ws_source = config.get_value("enterprise_search.source_id")
        self.enable_document_permission = config.get_value("enable_document_permission")
        self.user_mapping = config.get_value("networkdrive_enterprisesearch.user_mapping")

    def remove_all_permissions(self):
        """ Removes all the permissions present in the workplace
        """
        try:
            user_permission = self.workplace_search_client.list_permissions(
                content_source_id=self.ws_source,
            )

            if user_permission:
                self.logger.info("Removing the permissions from the workplace...")
                permission_list = user_permission['results']
                for permission in permission_list:
                    self.workplace_search_client.remove_user_permissions(
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
            self.workplace_search_client.add_user_permissions(
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
            with open(self.user_mapping) as mapping_file:
                try:
                    csvreader = csv.reader(mapping_file)
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
            self.logger.error(f'Could not find the users mapping file at the location: {self.user_mapping} or the file is empty. \
                Please add the sid->user mappings to sync the permissions in the Enterprise Search')
            raise EmptyMappingException

    def execute(self):
        """ Runs the permission indexing logic
        """
        self.logger.info("Starting the permission indexing..")
        if not self.enable_document_permission:
            self.logger.warning('Exiting as the enable permission flag is set to False')
            raise PermissionSyncDisabledException
        self.sync_permissions()
