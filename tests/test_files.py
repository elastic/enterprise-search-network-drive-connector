from unittest.mock import Mock
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from ees_network_drive.configuration import Configuration  # noqa
from ees_network_drive.indexing_rule import IndexingRules  # noqa
from ees_network_drive.files import Files  # noqa
from ees_network_drive.network_drive_client import NetworkDrive  # noqa


CONFIG_FILE = os.path.join(
    os.path.join(os.path.dirname(__file__), "config"),
    "network_drive_connector.yml",
)


def settings():
    """This function loads config from the file and returns it."""
    configuration = Configuration(file_name=CONFIG_FILE)

    logger = logging.getLogger("unit_test_indexing")
    return configuration, logger


def test_is_file_present_on_network_drive():
    """Test that is_file_present_on_network_drive Checks that folder/file present in Network Drives or not."""
    config, logger = settings()
    network_drive_client = NetworkDrive(config, logger)
    files_obj = Files(logger, config, network_drive_client)
    file_structure = {"Users/dummy/folder1": {"file1": "/dummy/folder1"}}
    mock_response = Mock(filename="file1")
    files_obj.network_drives_client.connect = Mock()
    files_obj.network_drives_client.connect.listPath = Mock(
        return_value=[mock_response]
    )
    response = files_obj.is_file_present_on_network_drive(
        files_obj.network_drives_client.connect,
        "TEST_SERVER",
        "Users/dummy/folder1",
        file_structure,
        [],
        [],
        [],
    )
    assert not response
