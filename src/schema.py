# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import datetime
from src.constant import DATETIME_FORMAT


def validate_date_new(input_date):
    if input_date:
        return datetime.datetime.strptime(input_date, DATETIME_FORMAT)


schema = {
    'network_drive.domain': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'network_drive.username': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'network_drive.password': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'network_drive.path': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'network_drive.server_name': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'network_drive.server_ip': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'client_machine.name': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'enterprise_search.access_token': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'enterprise_search.source_id': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'enterprise_search.host_url': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'include': {
        'nullable': True,
        'type': 'dict',
        'schema': {
            'path_template': {
                'nullable': True,
                'type': 'list',
                'schema': {
                    'type': 'string',
                }
            },
            'size': {
                'nullable': True,
                'type': 'list',
                'schema': {
                    'type': 'string',
                    'regex': '[>,<,=,!]=?([0-9]*)$',
                }
            },
        }
    },
    'exclude': {
        'nullable': True,
        'type': 'dict',
        'schema': {
            'path_template': {
                'nullable': True,
                'type': 'list',
                'schema': {
                    'type': 'string',
                }
            },
            'size': {
                'nullable': True,
                'type': 'list',
                'schema': {
                    'type': 'string',
                    'regex': '[>,<,=,!]=?([0-9]*)$'
                }
            }
        }
    },
    'start_time': {
        'required': False,
        'type': 'datetime',
        'max': datetime.datetime.utcnow(),
        'default': (datetime.datetime.utcnow() - datetime.timedelta(days=180)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'coerce': validate_date_new
    },
    'end_time': {
        'required': False,
        'type': 'datetime',
        'max': datetime.datetime.utcnow(),
        'default': (datetime.datetime.utcnow()).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'coerce': validate_date_new
    },
    'indexing_interval': {
        'required': False,
        'type': 'integer',
        'default': 60,
        'min': 1
    },
    'deletion_interval': {
        'required': False,
        'type': 'integer',
        'default': 60,
        'min': 1
    },
    'full_sync_interval': {
        'required': False,
        'type': 'integer',
        'default': 2880,
        'min': 1
    },
    'log_level': {
        'required': False,
        'type': 'string',
        'default': 'info',
        'allowed': ['debug', 'info', 'warn', 'error']
    },
    'retry_count': {
        'required': False,
        'type': 'integer',
        'default': 3,
        'min': 1
    },
    'worker_process': {
        'required': False,
        'type': 'integer',
        'default': 40,
        'min': 1
    },
    'enable_document_permission': {
        'required': False,
        'type': 'boolean',
        'default': True
    },
    'networkdrive_enterprisesearch.user_mapping': {
        'required': False,
        'type': 'string',
    },
    'sync_permission_interval': {
        'required': False,
        'type': 'integer',
        'default': 60,
        'min': 1
    }
}
