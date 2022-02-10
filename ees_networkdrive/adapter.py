#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Module containing default schema for data uploaded to Enterprise Search.

    This module contains definition of default schema for the data
    that will be uploaded to Elastic Enterprise Search per each Network Drive object.

    Keys for each object represent the fields that will be uploaded to Enterprise Search
    while key values represent Network Drive fields that will be used to populate the data.
"""
FILES = {
    'created_at': 'create_time',
    'id': 'file_id',
    'last_updated': 'updation_time',
    'path': 'file_path',
    'url': 'web_path',
    'title': 'file_name',
    'type': 'file_type',
    'size': 'file_size'
}
