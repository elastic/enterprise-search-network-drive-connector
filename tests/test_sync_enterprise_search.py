import pytest
from unittest.mock import Mock
import logging
from ees_network_drive.sync_enterprise_search import SyncEnterpriseSearch
from ees_network_drive.connector_queue import ConnectorQueue
from elastic_enterprise_search import WorkplaceSearch
from ees_network_drive.configuration import Configuration


def settings():
    """This function loads config from the file and returns it."""
    configuration = Configuration(file_name="network_drive_connector.yml")

    logger = logging.getLogger("unit_test_indexing")
    return configuration, logger


def create_enterprise_search_obj():
    """This function create Enterprise Search object for test."""
    configs, logger = settings()
    enterprise_search_host = configs.get_value("enterprise_search.host_url")
    workplace_search_client = WorkplaceSearch(
        enterprise_search_host,
        http_auth=configs.get_value("enterprise_search.api_key"),
    )
    queue = ConnectorQueue()
    return SyncEnterpriseSearch(configs, logger, workplace_search_client, queue)


@pytest.mark.parametrize(
    "documents, mock_response",
    [
        (
            [
                {
                    "id": 0,
                    "title": "file0",
                    "body": "Not much. It is a made up thing.",
                    "url": "dummy_folder/temp0.txt",
                    "created_at": "2019-06-01T12:00:00+00:00",
                    "type": "text",
                },
                {
                    "id": 1,
                    "title": "file1",
                    "body": "Not much. It is a made up thing.",
                    "url": "dummy_folder/temp1.txt",
                    "created_at": "2019-06-01T12:00:00+00:00",
                    "type": "text",
                },
            ],
            {"results": [{"id": "0", "errors": []}, {"id": "1", "errors": []}]},
        )
    ],
)
def test_index_document(documents, mock_response, caplog):
    """Test that index_document successfully index documents in workplace."""
    caplog.set_level("INFO")
    indexer_obj = create_enterprise_search_obj()
    indexer_obj.config._Configuration__configurations[
        "enterprise_search.host_url"
    ] = "dummy"
    indexer_obj.workplace_search_client.index_documents = Mock(
        return_value=mock_response
    )
    indexer_obj.index_documents(documents)
    assert "Successfully indexed 2 to the workplace out of 2" in caplog.text


@pytest.mark.parametrize(
    "documents, mock_response, log_level, error_msg",
    [
        (
            [
                {
                    "id": 0,
                    "title": "file0",
                    "body": "Not much. It is a made up thing.",
                    "url": "dummy_folder/temp0.txt",
                    "created_at": "2019-06-01T12:00:00+00:00",
                    "type": "text",
                }
            ],
            {"results": [{"id": "0", "errors": ["not indexed"]}]},
            "ERROR",
            "Unable to index the document with id: 0",
        )
    ],
)
def test_index_document_when_error_occurs(
    documents, mock_response, log_level, error_msg, caplog
):
    """Test that index_document give proper error message if document not indexed."""
    caplog.set_level(log_level)
    indexer_obj = create_enterprise_search_obj()
    indexer_obj.workplace_search_client.index_documents = Mock(
        return_value=mock_response
    )
    indexer_obj.index_documents(documents)
    assert error_msg in caplog.text


def test_index_document_with_invalid_credentials_of_workplace():
    """Test that index_document gives error when invalid credentials are provided for workplace."""
    indexer_obj = create_enterprise_search_obj()
    indexer_obj.config._Configuration__configurations[
        "enterprise_search.source_id"
    ] = "dummy"
    documents = [
        {
            "id": 0,
            "title": "file0",
            "body": "Not much. It is a made up thing.",
            "url": "dummy_folder/temp0.txt",
            "created_at": "2019-06-01T12:00:00+00:00",
            "type": "text",
        }
    ]
    with pytest.raises(Exception) as e_info:
        indexer_obj.index_documents(documents)
    assert "Content source 'dummy' does not exist" in str(e_info.value)
