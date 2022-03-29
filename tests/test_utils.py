import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from ees_network_drive.utils import split_list_into_buckets, fetch_users_from_csv_file, url_encode, split_documents_into_equal_chunks # noqa


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


def test_url_encode():
    """Tests url_encode performs encoding on the name of objects"""
    url_to_encode = '''http://ascii.cl?parameter="Click on 'URL Decode'!"'''
    result = url_encode(url_to_encode)
    encoded_url = (
        "http%3A%2F%2Fascii.cl%3Fparameter%3D%22Click%20on%20''URL%20Decode''%21%22"
    )
    assert result == encoded_url


def test_split_documents_into_equal_chunks():
    """Tests split_documents_into_equal_chunks splits a list or dictionary into equal chunks size"""
    list_to_split = ["1", "3", "4", "6", "7", "5", "8", "9", "2", "0", "111"]
    chunk_size = 3
    expected_result = [["1", "3", "4"], ["6", "7", "5"], ["8", "9", "2"], ["0", "111"]]
    result = split_documents_into_equal_chunks(list_to_split, chunk_size)
    assert expected_result == result
