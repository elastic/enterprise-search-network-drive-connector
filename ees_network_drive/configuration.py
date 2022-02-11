#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Configuration module allows manipulations with application configuration.

    This module can be used to read and validate configuration file that defines
    the settings of the Network Drive Server connector.
"""
import yaml
from cerberus import Validator
from yaml.error import YAMLError

from .constant import DATETIME_FORMAT
from .schema import schema


class ConfigurationInvalidException(Exception):
    """Exception raised when configuration was invalid.

    Attributes:
        errors - errors found in the configuration
        message -- explanation of the error
    """

    def __init__(self, errors):
        super().__init__(f"Provided configuration was invalid. Errors: {errors}.")

        self.errors = errors


class ConfigurationParsingException(Exception):
    """Exception raised when configuration could not be parsed.

    Attributes:
        file_name - name of the file that could not be parsed
    """

    def __init__(self, file_name, inner_exception):
        super().__init__("Failed to parse configuration file.")

        self.file_name = file_name
        self.inner_exception = inner_exception


class Configuration:
    """Configuration class is responsible for parsing, validating and accessing
    configuration options from connector configuration file."""

    def __init__(self, file_name):
        self.__configurations = {}
        self.file_name = file_name
        try:
            with open(file_name) as stream:
                self.__configurations = yaml.safe_load(stream)
        except YAMLError as exception:
            raise ConfigurationParsingException(file_name, exception)
        self.__configurations = self.validate()
        if self.__configurations["start_time"] >= self.__configurations["end_time"]:
            raise ConfigurationInvalidException(f"The start_time: {self.__configurations['start_time']}  \
                    cannot be greater than or equal to the end_time: {self.__configurations['end_time']}")

        for date_config in ["start_time", "end_time"]:
            value = self.__configurations[date_config]
            self.__configurations[date_config] = self.__parse_date_config_value(value)

    def validate(self):
        """Validates each properties defined in the yaml configuration file
        """
        validator = Validator(schema)
        validator.validate(self.__configurations, schema)
        if validator.errors:
            raise ConfigurationInvalidException(validator.errors)
        return validator.document

    def get_value(self, key):
        """Returns a configuration value that matches the key argument"""

        return self.__configurations.get(key)

    @staticmethod
    def __parse_date_config_value(string):
        return string.strftime(DATETIME_FORMAT)
