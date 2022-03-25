#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import pytest
import os
from unittest.mock import Mock
import argparse
import logging
from ees_network_drive.deletion_sync_command import DeletionSyncCommand
from ees_network_drive.configuration import Configuration
from ees_network_drive.network_drive_client import NetworkDrive
from ees_network_drive.files import Files

DUMMY_FILE_1 = "dummy/test.txt"
DUMMY_FILE_2 = "dummy/test1.txt"
CONFIG_FILE = os.path.join(
    os.path.join(os.path.dirname(__file__), "config"),
    "network_drive_connector.yml",
)


def settings():
    """This function loads config from the file and returns it"""
    configuration = Configuration(file_name=CONFIG_FILE)

    logger = logging.getLogger("unit_test_deletion_sync")
    return configuration, logger


@pytest.mark.parametrize(
    "ids, drive_name, expected_ids",
    [
        (
            {
                "global_keys": {
                    "dummy": {
                        "files": {
                            "844424930334011": DUMMY_FILE_1,
                            "543528180028451862": DUMMY_FILE_2,
                        }
                    }
                },
                "delete_keys": {
                    "dummy": {
                        "files": {
                            "844424930334011": DUMMY_FILE_1,
                            "543528180028451862": DUMMY_FILE_2,
                        }
                    }
                },
            },
            "dummy",
            ["844424930334011", "543528180028451862"],
        ),
        (
            {
                "global_keys": {
                    "dummy": {
                        "files": {
                            "844424930334011": DUMMY_FILE_1,
                            "543528180028451862": DUMMY_FILE_2,
                        }
                    }
                },
                "delete_keys": {"dummy": {"files": {}}},
            },
            "dummy",
            [],
        ),
    ],
)
@pytest.mark.skip(reason="Skipping since we need to mock smb server for this test")
def test_get_deleted_files(ids, drive_name, expected_ids):
    """Test get_deleted_files returns ids of deleted files from the Network Drives."""
    configs, logger = settings()
    network_drive_client = NetworkDrive(configs, logger)
    args = argparse.Namespace()
    args.config_file = CONFIG_FILE
    deletion_sync_obj = DeletionSyncCommand(args)
    file_ojb = Files(logger, configs, network_drive_client)
    file_ojb.check_file_in_network_drive = Mock(return_value=True)
    result = deletion_sync_obj.get_deleted_files(drive_name, ids)
    assert result == expected_ids


@pytest.mark.skip(reason="Skipping since we need to mock smb server for this test")
def test_get_deleted_files_with_invalid_credentials_of_workplace():
    """Test that get_deleted_files gives error when invalid credentials are provided for workplace."""
    ids = {
        "global_keys": {
            "dummy": {
                "files": {
                    "844424930334011": DUMMY_FILE_1,
                    "543528180028451862": DUMMY_FILE_2,
                }
            }
        },
        "delete_keys": {
            "dummy": {
                "files": {
                    "844424930334011": DUMMY_FILE_1,
                    "543528180028451862": DUMMY_FILE_2,
                }
            }
        },
    }
    expected_ids = {
        "global_keys": {
            "dummy": {
                "files": {
                    "844424930334011": DUMMY_FILE_1,
                    "543528180028451862": DUMMY_FILE_2,
                }
            }
        },
        "delete_keys": {
            "dummy": {
                "files": {
                    "844424930334011": DUMMY_FILE_1,
                    "543528180028451862": DUMMY_FILE_2,
                }
            }
        },
    }
    configs, logger = settings()
    network_drive_client = NetworkDrive(configs, logger)
    args = argparse.Namespace()
    args.config_file = CONFIG_FILE
    deletion_sync_obj = DeletionSyncCommand(args)
    deletion_sync_obj.config._Configuration__configurations[
        "enterprise_search.host_url"
    ] = "dummy"
    file_ojb = Files(logger, configs, network_drive_client)
    file_ojb.is_file_present_on_network_drive = Mock(return_value=True)
    deletion_sync_obj.get_deleted_files("dummy", ids)
    assert ids == expected_ids


@pytest.mark.parametrize(
    "ids, deleted_ids",
    [
        (
            {
                "global_keys": {
                    "CLIENT": {
                        "files": {
                            "844424930334011": DUMMY_FILE_1,
                            "543528180028451862": DUMMY_FILE_2,
                        }
                    }
                }
            },
            ["844424930334011", "543528180028451862"],
        )
    ],
)
@pytest.mark.skip(reason="Skipping since we need to mock smb server for this test")
def test_sync_deleted_files(ids, deleted_ids):
    """Test that sync_deleted_files delete files from Enterprise Search."""
    expected_ids = {"global_keys": {"CLIENT": {"files": {}}}}
    args = argparse.Namespace()
    args.config_file = CONFIG_FILE
    deletion_sync_obj = DeletionSyncCommand(args)
    deletion_sync_obj.workplace_search_client.delete_documents = Mock(return_value=True)
    result = deletion_sync_obj.sync_deleted_files(deleted_ids, ids)
    assert result == expected_ids
