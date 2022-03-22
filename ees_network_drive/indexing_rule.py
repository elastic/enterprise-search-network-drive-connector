#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""The module defines methods used to check the rules to be followed while indexing the objects to
    Enterprise Search.
"""
import re

from wcmatch import glob


class IndexingRules:
    """This class holds methods used to apply indexing filters on the documents to be indexed
    """

    def __init__(self, config):
        self.include = config.get_value("include")
        self.exclude = config.get_value("exclude")

    def filter_size(self, file_details, symbol, pattern):
        """This method is used to find if the file size is matching with the pattern
            :param file_details: dictionary containing file properties
            :param symbol: >,<,>=,<=,!,!=,=,== symbol
            :param pattern: numeric part of pattern as a string
            :returns: True or False denoting whether the file size is according to the pattern
        """
        file_size = file_details['file_size']
        int_value = int(pattern)
        operation = {
            '>': file_size > int_value,
            '>=': file_size >= int_value,
            '<': file_size < int_value,
            '<=': file_size <= int_value,
            '!': file_size != int_value,
            '!=': file_size != int_value,
            '=': file_size == int_value,
            '==': file_size == int_value,
        }
        return operation.get(symbol)

    def should_index(self, file_details):
        """This method is used to check if the current file is following the indexing rule or not
            :param file_details: dictionary containing file properties
            :param include: include pattern provided for matching
            :param exclude: exclude pattern for matching
            :returns: True or False denoting if the file is to following the indexing rule or not
        """
        should_include, should_exclude = True, True
        if self.include:
            should_include = self.should_include_or_exclude(self.include, {}, file_details, 'include')
        if self.exclude:
            should_exclude = self.should_include_or_exclude(self.exclude, self.include, file_details, 'exclude')
        return should_include and should_exclude

    def should_include_or_exclude(self, pattern_dict, is_present_in_include, file_details, pattern_type):
        """Function to decide wether to include the file or exclude it based on the indexing rules defined in the configuration
           :param pattern_dict: Dictionary containing key value pairs as filter type and list of patterns
           :param is_present_in_include: Used to check if any pattern is already present in include type
           :param file_details: dictionary containing file properties
           :param pattern_type: include/exclude
        """
        should_index = True
        for filtertype, pattern in pattern_dict.items():
            for value in (pattern or []):
                if is_present_in_include and (value in (is_present_in_include.get(filtertype) or [])):
                    pattern.remove(value)
            result = self.follows_indexing_rule(filtertype, pattern, file_details, pattern_type)
            if result is False:
                should_index = False
            elif result is True:
                return True
        return should_index

    def follows_indexing_rule(self, filtertype, pattern, file_details, pattern_type):
        """Applies filters on the file and returns True or False based on whether
           it follows the pattern or not
            :filtertype: denotes the type of filter used: size/path_template
            :param pattern: include/ exclude pattern provided for matching
            :param file_details: dictionary containing file properties
            :param pattern_type: include/exclude
        """
        if pattern:
            for value in pattern:
                if filtertype == 'size':
                    initial = re.match('[><=!]=?', value)
                    result = self.filter_size(file_details, initial[0], re.findall("[0-9]+", value)[0])
                else:
                    result = glob.globmatch(file_details['file_path'], value, flags=glob.GLOBSTAR)
                if (pattern_type == 'include' and result) or (pattern_type == 'exclude' and not(result)):
                    return True

            return False
