import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from ees_network_drive.utils import split_list_into_buckets, fetch_users_from_csv_file  # noqa


def test_split_list_into_buckets():
    """Test that split_list_into_buckets method divide large number of documents amongst the total buckets."""
    documents = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    total_bucket = 3
    expected_result = [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
    result = split_list_into_buckets(documents, total_bucket)
    assert result == expected_result


def test_fetch_users_from_csv_file():
    """Test that fetch_users_from_csv_file method create dictionary of sid and username from csv file."""
    logger = logging.getLogger("unit_test_utils")
    file_path = os.path.join(
        os.path.join(os.path.dirname(__file__), "config"),
        "user_mapping.csv",
    )

    expected_result = {"sid-123": "user1", "sid-456": "user2"}
    result = fetch_users_from_csv_file(file_path, logger)
    assert result == expected_result
