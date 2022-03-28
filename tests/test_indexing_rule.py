import pytest
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from ees_network_drive.indexing_rule import IndexingRules # noqa
from ees_network_drive.configuration import Configuration # noqa

CONFIG_FILE = os.path.join(
    os.path.join(os.path.dirname(__file__), "config"),
    "network_drive_connector.yml",
)


def settings():
    """This function loads config from the file and returns it."""
    configuration = Configuration(file_name=CONFIG_FILE)

    logger = logging.getLogger("unit_test_indexing_rules")
    return configuration, logger


@pytest.mark.parametrize(
    "file_details",
    [
        {
            "id": 0,
            "title": "file0",
            "body": "Not much. It is a made up thing.",
            "created_at": "2019-06-01T12:00:00+00:00",
            "type": "text",
            "file_path": "dummy_folder/file0.txt",
            "file_size": 23000
        }
    ],
)
def test_should_index_when_indexing_rules_not_followed(file_details):
    """Test that should_index returns False if the file does not follow the indexing rule"""
    config, logger = settings()
    indexing_rules_obj = IndexingRules(config)
    result = indexing_rules_obj.should_index(file_details)
    assert result == False


@pytest.mark.parametrize(
    "file_details",
    [
        {
            "id": 1,
            "title": "file1",
            "body": "This is just a test.",
            "created_at": "2020-06-01T12:00:00+00:00",
            "type": "png",
            "file_path": "dummy_folder_1/file1.png",
            "file_size": 3000
        }
    ],
)
def test_should_index_when_indexing_rule_is_followed(file_details):
    """"Test that should_index returns True if the file follows the indexing rule"""
    config, logger = settings()
    indexing_rules_obj = IndexingRules(config)
    result = indexing_rules_obj.should_index(file_details)
    assert result == True