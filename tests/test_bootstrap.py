import os
from unittest.mock import Mock
import argparse
import logging
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from ees_network_drive.bootstrap_command import BootstrapCommand  # noqa
from elastic_enterprise_search import WorkplaceSearch  # noqa
from ees_network_drive.configuration import Configuration  # noqa

CONFIG_FILE = os.path.join(
    os.path.join(os.path.dirname(__file__), "config"),
    "network_drive_connector.yml",
)


def settings():
    """This function loads config from the file and returns it."""
    configuration = Configuration(file_name=CONFIG_FILE)

    logger = logging.getLogger("unit_test_bootstrap_command")
    return configuration, logger


def test_execute(caplog):
    """Test execute method in Bootstrap file creates a content source in the Enterprise Search."""
    args = argparse.Namespace()
    args.name = "dummy"
    args.config_file = CONFIG_FILE
    caplog.set_level("INFO")
    mock_response = {"id": "1234"}
    bootstrap_obj = BootstrapCommand(args)
    bootstrap_obj.workplace_search_custom_client.workplace_search_client.create_content_source = Mock(
        return_value=mock_response
    )
    bootstrap_obj.execute()
    assert "Created ContentSource with ID 1234." in caplog.text


def test_execute_with_user_argument(caplog):    
    """Test execute method in Bootstrap file creates a content source using user argument in the Enterprise Search."""
    args = argparse.Namespace()
    args.name = "dummy"
    args.user = "user1"
    args.password = "user123"
    args.config_file = CONFIG_FILE
    caplog.set_level("INFO")
    mock_response = {"id": "1234"}
    bootstrap_obj = BootstrapCommand(args)
    bootstrap_obj.workplace_search_custom_client.workplace_search_client.create_content_source = Mock(
        return_value=mock_response
    )
    bootstrap_obj.execute()
    assert "Created ContentSource with ID 1234." in caplog.text