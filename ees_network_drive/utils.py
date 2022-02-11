#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module contains uncategorisied utility methods.
"""
import hashlib
import time
import urllib.parse

from tika import parser


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
        :param file_name: name of the file in the Network Drive
        :param file_path: path ofthe file in the Network Drive
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
                        'Error while connecting to the network drive. Retry count: %s out of %s. \
                            Error: %s' % (retry, self.retry_count, exception)
                    )
                    time.sleep(2 ** retry)
                    retry += 1
        return execute
    return decorator
