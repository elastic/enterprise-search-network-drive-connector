# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import os
import json
from src import constant
from src.base_class import BaseClass


class Checkpoint(BaseClass):
    def __init__(self, logger):
        BaseClass.__init__(self, logger=logger)
        self.logger = logger

    def get_checkpoint(self, current_time, drive):
        """This method fetches the checkpoint from the checkpoint file in
           the local storage. If the file does not exist, it takes the
           checkpoint details from the configuration file.
           :param current_time: current time
           :param drive: drive for which checkpoint is fetched
        """
        self.logger.info(
            "Fetching the checkpoint details from the checkpoint file: %s"
            % constant.CHECKPOINT_PATH
        )

        start_time = self.configurations.get("start_time")
        end_time = self.configurations.get("end_time")

        if os.path.exists(constant.CHECKPOINT_PATH) and os.path.getsize(constant.CHECKPOINT_PATH) > 0:
            self.logger.info(
                "Checkpoint file exists and has contents, hence considering the checkpoint time instead of start_time and end_time"
            )
            with open(constant.CHECKPOINT_PATH, encoding="UTF-8") as checkpoint_store:
                try:
                    checkpoint_list = json.load(checkpoint_store)

                    if not checkpoint_list.get(drive):
                        self.logger.info(
                            f"The checkpoint file is present but it does not contain the start_time for {drive}, hence considering the start_time and end_time from the configuration file instead of the last successful fetch time"
                        )
                    else:
                        start_time = checkpoint_list.get(drive)
                        end_time = current_time
                except ValueError as exception:
                    self.logger.exception(
                        f"Error while parsing the json file of the checkpoint store from path: {constant.CHECKPOINT_PATH}. Error: {exception}"
                    )
                    self.logger.info(
                        "Considering the start_time and end_time from the configuration file"
                    )

        else:
            self.logger.info(
                f"Checkpoint file does not exist at {constant.CHECKPOINT_PATH}, considering the start_time and end_time from the configuration file"
            )

        self.logger.info(
            f"Contents of the start_time: {start_time} and end_time: {end_time}",
        )
        return start_time, end_time

    def set_checkpoint(self, current_time, index_type, drive):
        """ This method updates the existing checkpoint json file or creates
            a new checkpoint json file in case it is not present
            :param current_time: current time
            :index_type: indexing type from "incremental" or "full_sync"
            :param drive: object type to set the checkpoint
        """
        if os.path.exists(constant.CHECKPOINT_PATH) and os.path.getsize(constant.CHECKPOINT_PATH) > 0:
            self.logger.info(
                f"Setting the checkpoint contents: {current_time} for the to the checkpoint path: {constant.CHECKPOINT_PATH}"
            )
            with open(constant.CHECKPOINT_PATH, encoding="UTF-8") as checkpoint_store:
                try:
                    checkpoint_list = json.load(checkpoint_store)
                    checkpoint_list[drive] = current_time
                except ValueError as exception:
                    self.logger.exception(
                        f"Error while parsing the json file of the checkpoint store from path: {constant.CHECKPOINT_PATH}. Error: {exception}"
                    )

        else:
            if index_type == "incremental":
                checkpoint_time = self.configurations.get("end_time")
            else:
                checkpoint_time = current_time
            self.logger.info(
                f"Setting the checkpoint contents: {checkpoint_time} for the to the checkpoint path: {constant.CHECKPOINT_PATH}"
            )
            checkpoint_list = {drive: checkpoint_time}

        with open(constant.CHECKPOINT_PATH, "w", encoding="UTF-8") as checkpoint_store:
            try:
                json.dump(checkpoint_list, checkpoint_store, indent=4)
            except ValueError as exception:
                self.logger.exception(
                    f"Error while updating the existing checkpoint json file. Adding the new content directly instead of updating. Error: {exception}"
                )

        self.logger.info("Successfully saved the checkpoint")
