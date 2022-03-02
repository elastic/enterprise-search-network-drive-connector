#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module contains all the constants used throughout the code.
"""
import os

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
IDS_PATH = os.path.join(os.path.dirname(__file__), 'doc_id.json')
BATCH_SIZE = 100
