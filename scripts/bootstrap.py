# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import argparse
import getpass
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from elastic_enterprise_search import WorkplaceSearch
import src.logger_manager as log
from src.base_class import BaseClass
logger = log.setup_logging("network_drive_connector_bootstrap")


class BootStrap(BaseClass):
    def __init__(self):
        BaseClass.__init__(self, logger=logger)

    def bootstraping(self):
        """ This method is used to create a new content source in Enterprise Search.
        """
        parser = argparse.ArgumentParser(
            description='Create a custom content source.')
        parser.add_argument("--name", required=True, type=str,
                            help="Name of the content source to be created")
        parser.add_argument("--user", required=False, type=str,
                            help="username of the workplce search admin account ")

        host = self.configurations.get("enterprise_search.host_url")
        args = parser.parse_args()
        if args.user:
            password = getpass.getpass(prompt='Password: ', stream=None)
            workplace_search = WorkplaceSearch(
                f"{host}/api/ws/v1/sources", http_auth=(args.user, password)
            )
        else:
            workplace_search = WorkplaceSearch(
                f"{host}/api/ws/v1/sources", http_auth=self.configurations.get("enterprise_search.access_token")
            )
        try:
            resp = workplace_search.create_content_source(
                body={
                    "name": args.name,
                    "schema": {
                        "title": "text",
                        "body": "text",
                        "url": "text",
                        "created_at": "date",
                        "name": "text",
                        "description": "text",
                        "type": "text",
                        "size": "text"
                    },
                    "display": {
                        "title_field": "title",
                        "description_field": "description",
                        "url_field": "url",
                        "detail_fields": [
                            {"field_name": 'created_at', "label": 'Created At'},
                            {"field_name": 'type', "label": 'Type'},
                            {"field_name": 'size', "label": 'Size'},
                            {"field_name": 'description', "label": 'Description'},
                            {"field_name": 'body', "label": 'Content'}
                        ],
                        "color": "#000000"
                    },
                    "is_searchable": True
                }
            )

            content_source_id = resp.get('id')
            print(
                f"Created ContentSource with ID {content_source_id}. You may now begin indexing with content-source-id= {content_source_id}")
        except Exception as exception:
            print("Could not create a content source, Error %s" % (exception))


if __name__ == "__main__":
    BootStrap().bootstraping()
