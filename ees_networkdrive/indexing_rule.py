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

    def apply_rules(self, file_details, include, exclude):
        """This method is used to check if the current file is following the indexing rule or not
            :param file_details: dictionary containing file properties
            :param include: include pattern provided for matching
            :param exclude: exclude pattern for matching
            :returns: True or False denoting if the file is to following the indexing rule or not
        """
        inc, exc = True, True
        if include:
            inc = self.include_exclude(include, {}, file_details, 'include')
        if exclude:
            exc = self.include_exclude(exclude, include, file_details, 'exclude')
        return inc and exc

    def include_exclude(self, pattern_dict, is_present_in_include, file_details, pattern_type):
        """Helper function used to redirect the filtering based on filtertype(size/path)
           and pattern type(include/exclude)
           :param pattern_dict: Dictionary containing key value pairs as filter type and list of patterns
           :param is_present_in_include: Used to check if any pattern is already present in include type
           :param file_details: dictionary containing file properties
           :param pattern_type: include/exclude
        """
        for filtertype, pattern in pattern_dict.items():
            for value in (pattern or []):
                if is_present_in_include and (value in (is_present_in_include.get(filtertype) or [])):
                    pattern.remove(value)
            result = self.filter_pattern(filtertype, pattern, file_details, pattern_type)
            if result is True:
                return True
        if result is None:
            return True
        return False

    def filter_pattern(self, filtertype, pattern, file_details, pattern_type):
        """This method is used to connect with Network Drives.
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
