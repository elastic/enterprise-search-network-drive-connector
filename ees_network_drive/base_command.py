#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Module contains a base command interface.

Connector can run multiple commands such as full-sync, incremental-sync,
etc. This module provides convenience interface defining the shared
objects and methods that will can be used by commands."""
import logging

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from concurrent.futures import ThreadPoolExecutor, as_completed

from .configuration import Configuration
from .enterprise_search_wrapper import EnterpriseSearchWrapper
from .indexing_rule import IndexingRules
from .local_storage import LocalStorage
from .network_drive_client import NetworkDrive


class BaseCommand:
    """Base interface for all module commands.
    Inherit from it and implement 'execute' method, then add
    code to cli.py to register this command."""

    def __init__(self, args):
        self.args = args

    def execute(self):
        """Run the command.
        This method is overridden by actual commands with logic
        that is specific to each command implementing it."""
        raise NotImplementedError

    @cached_property
    def logger(self):
        """Get the logger instance for the running command.
        log level will be determined by the configuration
        setting log_level.
        """
        log_level = self.config.get_value('log_level')
        logger = logging.getLogger(__name__)
        logger.propagate = True
        logger.setLevel(log_level)

        handler = logging.StreamHandler()
        # Uncomment the following lines to output logs in ECS-compatible format
        # formatter = ecs_logging.StdlibFormatter()
        # handler.setFormatter(formatter)
        handler.setLevel(log_level)
        logger.addHandler(handler)

        return logger

    @cached_property
    def workplace_search_custom_client(self):
        """Get the workplace search custom client instance for the running command.
        """
        return EnterpriseSearchWrapper(self.logger, self.config, self.args)

    @cached_property
    def config(self):
        """Get the configuration for the connector for the running command."""
        file_name = self.args.config_file
        return Configuration(file_name)

    @cached_property
    def network_drive_client(self):
        """Get the Network Drives client instance for the running command."""
        return NetworkDrive(self.config, self.logger)

    @cached_property
    def indexing_rules(self):
        """Get the object for indexing rules to check should the file be indexed or not
            based on the patterns defined in configuration file.
        """
        return IndexingRules(self.config)

    def create_jobs(self, thread_count, func, args, iterable_list):
        """Apply async calls using multithreading to the targeted function
        :param thread_count: Total number of threads to be spawned
        :param func: The target function on which the async calls would be made
        :param args: Arguments for the targeted function
        :param iterable_list: list to iterate over and create thread
        """
        documents = {}
        # If iterable_list is present, then iterate over the list and pass each list element
        # as an argument to the async function, else iterate over number of threads configured
        if iterable_list:
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                future_to_path = {executor.submit(func, *args, list_element):
                                  list_element for list_element in iterable_list}

                for future in as_completed(future_to_path):
                    path = future_to_path[future]
                    try:
                        documents.update(future.result())
                    except Exception as exception:
                        self.logger.exception(f"Error while fetching in path {path}. Error {exception}")
        else:
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                for _ in range(thread_count):
                    executor.submit(func)
        return documents

    @cached_property
    def local_storage(self):
        """Get the object for local storage to fetch and update ids stored locally
        """
        return LocalStorage(self.logger)
