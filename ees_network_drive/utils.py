#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module contains un-categorized utility methods.
"""
import hashlib
import time
import csv
import os
import urllib.parse

from datetime import datetime
from tika import parser

from .constant import RFC_3339_DATETIME_FORMAT


def extract(content):
    """ Extracts the contents
        :param content: content to be extracted
        Returns:
            parsed_test: parsed text
    """
    parsed = parser.from_buffer(content)
    parsed_text = parsed['content']
    return parsed_text


def url_encode(object_name):
    """ Performs encoding on the name of objects
        containing special characters in their url, and
        replaces single quote with two single quote since quote
        is treated as an escape character in odata
        :param object_name: name that contains special characters
    """
    name = urllib.parse.quote(object_name, safe="'")
    return name.replace("'", "''")


def hash_id(file_name, file_path):
    """ Hashes the file_name and path to create file id if file id
        is not present
        :param file_name: name of the file in the Network Drives
        :param file_path: path of the file in the Network Drives
        :Returns: hashed file id
    """
    return hashlib.sha256(file_name + '-' + file_path).hexdigest()


def retry(exception_list):
    """ Decorator for retrying in case of network exceptions.
        Retries the wrapped method `times` times if the exceptions listed
        in ``exceptions`` are thrown
        :param exception_list: Lists of exceptions on which the connector should retry
    """
    def decorator(func):
        def execute(self, *args, **kwargs):
            retry = 1
            while retry <= self.retry_count:
                try:
                    return func(self, *args, **kwargs)
                except exception_list as exception:
                    self.logger.exception(
                        f'Error while creating a connection. Retry count: {retry} out of {self.retry_count}. \
                            Error: {exception}'
                    )
                    time.sleep(2 ** retry)
                    retry += 1
        return execute
    return decorator


def fetch_users_from_csv_file(user_mapping, logger):
    """This method is used to map sid to username from csv file.
        :param user_mapping: path to csv file containing network drives to enterprise search mapping
        :param logger: logger object
        :returns: dictionary of sid and username
    """
    rows = {}
    if (user_mapping and os.path.exists(user_mapping) and os.path.getsize(user_mapping) > 0):
        with open(user_mapping, encoding='utf-8') as mapping_file:
            try:
                csvreader = csv.reader(mapping_file)
                for row in csvreader:
                    rows[row[0]] = row[1]
            except csv.Error as e:
                logger.exception(f"Error while reading user mapping file at the location: {user_mapping}. Error: {e}")
    return rows


def split_in_chunks(input_list, chunk_size):
    """This method splits a list into separate chunks with maximum size
        as chunk_size
        :param input_list: list to be partitioned into chunks
        :param chunk_size: maximum size of a chunk
        Returns:
            :list_of_chunks: list containing the chunks
    """
    list_of_chunks = []
    for i in range(0, len(input_list), chunk_size):
        list_of_chunks.append(input_list[i:i + chunk_size])
    return list_of_chunks


def group_files_by_folder_path(file_details):
    """This method returns a dictionary of folder paths and list of files inside the folder
        :param file_details: dictionary containing file id and file path
        Returns:
            file_structure: dictionary containing folder and list of files inside the folder
    """
    file_structure = {}
    if file_details:
        for file_id, file_path in file_details.items():
            file_path, file_name = os.path.split(file_path)
            if file_structure.get(file_path):
                file_structure[file_path][file_name] = file_id
            else:
                file_structure[file_path] = {file_name: file_id}
    return file_structure


def get_current_time():
    """Returns current time in rfc 3339 format
    """
    return (datetime.utcnow()).strftime(RFC_3339_DATETIME_FORMAT)
