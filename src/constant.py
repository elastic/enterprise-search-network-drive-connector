# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import os

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), 'checkpoint.json')
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
IDS_PATH = os.path.join(os.path.dirname(__file__), 'doc_id.json')
CONFIG_FILE = "network_drive_connector_config.yml"
DOCUMENT_SIZE = 100
USE_NTLM_V2 = True
IS_DIRECT_TCP = True
SERVER_PORT = 445
STATUS_NO_SUCH_FILE = 3221225487
STATUS_NO_SUCH_DEVICE = 3221225486
STATUS_OBJECT_NAME_NOT_FOUND = 3221225524
STATUS_OBJECT_PATH_NOT_FOUND = 3221225530
ACCESS_ALLOWED_TYPE = 0
ACCESS_DENIED_TYPE = 1
ACCESS_MASK_DENIED_WRITE_PERMISSION = 278
ACCESS_MASK_ALLOWED_WRITE_PERMISSION = 1048854
