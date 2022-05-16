#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import os
import sys

import pytest
import argparse
import logging
from unittest.mock import Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ees_network_drive.configuration import Configuration   # noqa
from ees_network_drive.deletion_sync_command import DeletionSyncCommand     # noqa


ROOT_DIR_FILE = '/file_in_root.txt'
FILE_1_IN_PARENT_FOLDER = '/folder_in_root/file1.txt'
FILE_2_IN_PARENT_FOLDER = '/folder_in_root/file2.txt'
FILE_3_IN_SUB_FOLDER = '/folder_in_root/folder_in_folder_with_files/file3.txt'
FILE_4_IN_SUB_FOLDER = '/folder_in_root/folder_in_folder_with_files/file4.txt'
EMPTY_SUB_FOLDER = '/folder_in_root/folder_in_folder_with_no_files/'

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
    "ids, drive_name",
    [
        (
            {
                "global_keys": {
                    "files": {
                        "844424930334011": ROOT_DIR_FILE,
                        "543528180028451862": FILE_1_IN_PARENT_FOLDER,
                        "840733669383922639": FILE_2_IN_PARENT_FOLDER,
                        "557788652057687615": FILE_3_IN_SUB_FOLDER,
                        "627114226410696732": FILE_4_IN_SUB_FOLDER,
                    }
                },
                "delete_keys": {
                    "files": {
                        "844424930334011": ROOT_DIR_FILE,
                        "543528180028451862": FILE_1_IN_PARENT_FOLDER,
                        "840733669383922639": FILE_2_IN_PARENT_FOLDER,
                        "557788652057687615": FILE_3_IN_SUB_FOLDER,
                        "627114226410696732": FILE_4_IN_SUB_FOLDER,
                    }
                },
            },
            "dummy",
        ),
    ],
)
def test_get_deleted_files(ids, drive_name):
    """Test get_deleted_files raises exception if smb connection fails."""
    args = argparse.Namespace()
    args.config_file = CONFIG_FILE
    deletion_sync_obj = DeletionSyncCommand(args)
    deletion_sync_obj.network_drive_client.connect = Mock(return_value=False)
    with pytest.raises(Exception) as exception:
        deletion_sync_obj.get_deleted_files(drive_name, ids)
    assert str(exception.value) == "Unknown error while connecting to network drives"


@pytest.mark.parametrize(
    "ids, deleted_ids",
    [
        (
            {
                "global_keys": {
                    "files": {
                        "844424930334011": ROOT_DIR_FILE,
                        "543528180028451862": FILE_1_IN_PARENT_FOLDER,
                        "840733669383922639": FILE_2_IN_PARENT_FOLDER,
                        "557788652057687615": FILE_3_IN_SUB_FOLDER,
                        "627114226410696732": FILE_4_IN_SUB_FOLDER,
                    }
                },
                "delete_keys": {
                    "files": {
                        "844424930334011": ROOT_DIR_FILE,
                        "543528180028451862": FILE_1_IN_PARENT_FOLDER,
                        "840733669383922639": FILE_2_IN_PARENT_FOLDER,
                        "557788652057687615": FILE_3_IN_SUB_FOLDER,
                        "627114226410696732": FILE_4_IN_SUB_FOLDER,
                    }
                },
            },
            ["844424930334011", "543528180028451862", "627114226410696732"],
        )
    ],
)
def test_sync_deleted_files(ids, deleted_ids):
    """Test that sync_deleted_files delete files from Enterprise Search."""
    expected_ids = {
        "global_keys": {
            "files": {
                "840733669383922639": FILE_2_IN_PARENT_FOLDER,
                "557788652057687615": FILE_3_IN_SUB_FOLDER,
            }
        },
        "delete_keys": {
            "files": {
                "844424930334011": ROOT_DIR_FILE,
                "543528180028451862": FILE_1_IN_PARENT_FOLDER,
                "840733669383922639": FILE_2_IN_PARENT_FOLDER,
                "557788652057687615": FILE_3_IN_SUB_FOLDER,
                "627114226410696732": FILE_4_IN_SUB_FOLDER,
            }
        }
    }
    args = argparse.Namespace()
    args.config_file = CONFIG_FILE
    deletion_sync_obj = DeletionSyncCommand(args)
    deletion_sync_obj.workplace_search_custom_client.delete_documents = Mock(return_value=True)
    result = deletion_sync_obj.sync_deleted_files(deleted_ids, ids)
    assert result == expected_ids
