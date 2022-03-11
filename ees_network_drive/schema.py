#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""schema module contains Connector configuration file schema.
"""
import datetime

from .constant import DATETIME_FORMAT


def coerce_rfc_3339_date(input_date):
    """This function returns true if its argument is a valid RFC 3339 date."""
    if input_date:
        return datetime.datetime.strptime(input_date, DATETIME_FORMAT)
    return False


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
    'enterprise_search.api_key': {
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
                    'regex': '[><=!]=?([0-9]*)$',
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
                    'regex': '[><=!]=?([0-9]*)$'
                }
            }
        }
    },
    'start_time': {
        'required': False,
        'type': 'datetime',
        'max': datetime.datetime.utcnow(),
        'default': '1970-01-01T00:00:00Z',
        'coerce': coerce_rfc_3339_date
    },
    'end_time': {
        'required': False,
        'type': 'datetime',
        'max': datetime.datetime.utcnow(),
        'default': (datetime.datetime.utcnow()).strftime(DATETIME_FORMAT),
        'coerce': coerce_rfc_3339_date
    },
    'log_level': {
        'required': False,
        'type': 'string',
        'default': 'INFO',
        'allowed': ['DEBUG', 'INFO', 'WARNING', 'ERROR ']
    },
    'retry_count': {
        'required': False,
        'type': 'integer',
        'default': 3,
        'min': 1
    },
    'max_threads': {
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
    'network_drive_enterprise_search.user_mapping': {
        'required': False,
        'type': 'string',
    }
}
