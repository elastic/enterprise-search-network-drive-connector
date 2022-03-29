#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import pytest
import json
import datetime
import os
import logging
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ees_network_drive.checkpointing import Checkpoint # noqa
from ees_network_drive.constant import RFC_3339_DATETIME_FORMAT # noqa
from ees_network_drive.configuration import Configuration # noqa


CHECKPOINT_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "ees_network_drive",
    "checkpoint.json",
)


def settings():
    """This function loads config from the file and returns it."""
    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "network_drive_connector.yml",
        )
    )

    logger = logging.getLogger("unit_test_checkpointing")
    return configuration, logger


def test_set_checkpoint_when_checkpoint_file_available():
    """Test that set_checkpoint method set current time in checkpoint.json file \
        when checkpoint.json file is available."""
    configs, logger = settings()
    checkpoint_obj = Checkpoint(configs, logger)
    json_object = {
        "CLIENT": (datetime.datetime.utcnow() - datetime.timedelta(days=3)).strftime(
            RFC_3339_DATETIME_FORMAT
        )
    }
    with open(CHECKPOINT_PATH, "w") as outfile:
        json.dump(json_object, outfile, indent=4)
    current_time = (datetime.datetime.utcnow()).strftime(RFC_3339_DATETIME_FORMAT)
    checkpoint_obj.set_checkpoint(current_time, "incremental", "CLIENT")
    with open(CHECKPOINT_PATH, encoding="UTF-8") as checkpoint_store:
        checkpoint_list = json.load(checkpoint_store)
    assert checkpoint_list["CLIENT"] == current_time


@pytest.mark.parametrize(
    "index_type, expected_time, current_time, drive_name",
    [
        (
            "incremental",
            "2021-12-28T15:14:28Z",
            (datetime.datetime.utcnow()).strftime(RFC_3339_DATETIME_FORMAT),
            "dummy",
        ),
        (
            "full_sync",
            (datetime.datetime.utcnow()).strftime(RFC_3339_DATETIME_FORMAT),
            (datetime.datetime.utcnow()).strftime(RFC_3339_DATETIME_FORMAT),
            "dummy",
        ),
    ],
)
def test_set_checkpoint_when_checkpoint_file_not_available(
    index_type, expected_time, current_time, drive_name
):
    """Test that set_checkpoint method set correct time in checkpoint.json file \
        when checkpoint.json file is not available."""
    configs, logger = settings()
    checkpoint_obj = Checkpoint(configs, logger)
    checkpoint_obj.config._Configuration__configurations["end_time"] = expected_time
    if os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)

    checkpoint_obj.set_checkpoint(current_time, index_type, drive_name)
    with open(CHECKPOINT_PATH, encoding="UTF-8") as checkpoint_store:
        checkpoint_list = json.load(checkpoint_store)
    assert checkpoint_list[drive_name] == expected_time


def test_get_checkpoint_when_checkpoint_file_available():
    """Test that get_checkpoint method set current time in checkpoint.json file \
        when checkpoint.json file is available."""
    configs, logger = settings()
    checkpoint_obj = Checkpoint(configs, logger)
    checkpoint_time = (
        datetime.datetime.utcnow() - datetime.timedelta(days=3)
    ).strftime(RFC_3339_DATETIME_FORMAT)
    json_object = {"CLIENT": checkpoint_time}
    with open(CHECKPOINT_PATH, "w") as outfile:
        json.dump(json_object, outfile, indent=4)
    current_time = (datetime.datetime.utcnow()).strftime(RFC_3339_DATETIME_FORMAT)
    start_time, end_time = checkpoint_obj.get_checkpoint(current_time, "CLIENT")
    assert start_time == checkpoint_time
    assert end_time == current_time
