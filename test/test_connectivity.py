# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import time
import src.logger_manager as log
from src.configuration import Configuration
from src.utils import print_and_log
from src.network_drive_client import NetworkDrive
from elastic_enterprise_search import WorkplaceSearch
import pytest

logger = log.setup_logging("network_drive_connector_test")


@pytest.fixture
def settings():
    configuration = Configuration(logger=logger)
    configs = configuration.configurations
    return configs, configs.get("retry_count")


@pytest.mark.drives
def test_network_drive(settings):
    """ Tests the connection to the network drive server by calling a basic get request to fetch files and logs proper messages
    """
    configs, _ = settings
    logger.info("Starting Network Drive connectivity tests..")
    network_drive_client = NetworkDrive(logger)
    conn = network_drive_client.connect()

    if not conn:
        assert False, "Error while connecting to the Network Drive server at %s:445" % (
            configs.get("network_drive.server_ip"))
    else:
        assert True
    conn.close()
    logger.info("Network Drive connectivity tests completed..")


@pytest.mark.workplace
def test_workplace(settings):
    """ Tests the connection to the Enterprise search host
    """
    configs, retry_count = settings
    logger.info("Starting Workplace connectivity tests..")
    enterprise_search_host = configs.get("enterprise_search.host_url")
    retry = 0
    while retry <= retry_count:
        try:
            workplace_search = WorkplaceSearch(
                enterprise_search_host,
                http_auth=configs.get(
                    "enterprise_search.access_token"
                ),
            )
            response = workplace_search.get_content_source(
                content_source_id=configs.get(
                    "enterprise_search.source_id"
                )
            )
            if response:
                assert True
                break
        except Exception as exception:
            print_and_log(
                logger,
                "exception",
                "[Fail] Error while connecting to the workplace host %s. Retry Count: %s. Error: %s"
                % (
                    enterprise_search_host,
                    retry,
                    exception,
                ),
            )
            # This condition is to avoid sleeping for the last time
            if retry < retry_count:
                time.sleep(2 ** retry)
            else:
                assert False, "Error while connecting to the Enterprise Search at %s" % (
                    enterprise_search_host)
            retry += 1

    logger.info("Workplace connectivity tests completed..")


@pytest.mark.ingestion
def test_ingestion(settings):
    """ Tests the successful ingestion and deletion of a sample document to the Workplace search
    """
    configs, retry_count = settings
    enterprise_search_host = configs.get("enterprise_search.host_url")
    logger.info("Starting Workplace ingestion tests..")
    document = [
        {
            "id": 1234,
            "title": "The Meaning of Time",
            "body": "Not much. It is a made up thing.",
            "url": "https://example.com/meaning/of/time",
            "created_at": "2019-06-01T12:00:00+00:00",
            "type": "list",
        }
    ]
    workplace_search = WorkplaceSearch(enterprise_search_host)
    retry = 0
    response = None
    while retry <= retry_count:
        try:
            response = workplace_search.index_documents(
                http_auth=configs.get("enterprise_search.access_token"), content_source_id=configs.get("enterprise_search.source_id"),
                documents=document,
            )
            logger.info(
                "Successfully indexed a dummy document with id 1234 in the Workplace")
            break
        except Exception as exception:
            print_and_log(
                logger,
                "exception",
                "[Fail] Error while ingesting document to the workplace host %s. Retry Count: %s. Error: %s"
                % (
                    enterprise_search_host,
                    retry,
                    exception,
                ),
            )
            # This condition is to avoid sleeping for the last time
            if retry < retry_count:
                time.sleep(2 ** retry)
            else:
                assert False, "Error while connecting to the Enterprise Search at %s" % (
                    enterprise_search_host)
            retry += 1

    if response:
        logger.info(
            "Attempting to delete the dummy document 1234 from the Workplace for cleanup"
        )
        retry = 0
        while retry <= retry_count:
            try:
                response = workplace_search.delete_documents(
                    http_auth=configs.get(
                        "enterprise_search.access_token"
                    ),
                    content_source_id=configs.get(
                        "enterprise_search.source_id"
                    ),
                    document_ids=[1234],
                )
                logger.info(
                    "Successfully deleted the dummy document with id 1234 from the Workplace"
                )
                if response:
                    assert True
                    break
            except Exception as exception:
                print_and_log(
                    logger,
                    "exception",
                    "[Fail] Error while deleting document id 1234 from the workplace host %s. Retry Count: %s. Error: %s"
                    % (
                        enterprise_search_host,
                        retry,
                        exception,
                    ),
                )
                # This condition is to avoid sleeping for the last time
                if retry < retry_count:
                    time.sleep(2 ** retry)
                else:
                    assert False, "Error while connecting to the Enterprise Search at %s" % (
                        enterprise_search_host)
                retry += 1

    logger.info("Workplace ingestion tests completed..")
