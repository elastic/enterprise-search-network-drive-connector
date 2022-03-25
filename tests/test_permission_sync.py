#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
from unittest.mock import Mock
import logging
import argparse
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from ees_network_drive.permission_sync_command import PermissionSyncCommand  # noqa
from ees_network_drive.configuration import Configuration  # noqa

CONFIG_FILE = os.path.join(
    os.path.join(os.path.dirname(__file__), "config"),
    "network_drive_connector.yml",
)


def settings():
    """This function loads config from the file and returns it."""
    configuration = Configuration(file_name=CONFIG_FILE)

    logger = logging.getLogger("unit_test_permission_sync")
    return configuration, logger


def test_remove_all_permissions():
    """Test that remove_all_permissions remove all permissions from Enterprise Search."""
    args = argparse.Namespace()
    args.config_file = CONFIG_FILE
    permission_obj = PermissionSyncCommand(args)
    mocked_respose = {"results": [{"user": "user1", "permissions": "permission1"}]}
    permission_obj.workplace_search_client.list_permissions = Mock(
        return_value=mocked_respose
    )
    permission_obj.workplace_search_client.remove_user_permissions = Mock(
        return_value=True
    )
    permission_obj.remove_all_permissions()
    assert True


def test_workplace_add_permission(caplog):
    """Test that workplace_add_permission successfully add permission to Enterprise Search."""
    args = argparse.Namespace()
    args.config_file = CONFIG_FILE
    permission_obj = PermissionSyncCommand(args)
    permission_obj.workplace_search_client.add_user_permissions = Mock(
        return_value=True
    )
    permission_obj.workplace_add_permission("user1", "permission1")
    assert True
