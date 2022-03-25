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

    logger = logging.getLogger("unit_test_indexing")
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
            "file_path": "dummy_folder/temp0.txt",
            "file_size": 23000
        }
    ],
)
def test_should_index(file_details):
    """Test that index_document successfully index documents in workplace."""
    config, logger = settings()
    indexing_rules_obj = IndexingRules(config)
    result = indexing_rules_obj.should_index(file_details)
    assert result == False
