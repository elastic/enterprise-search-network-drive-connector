# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License
# 2.0; you may not use this file except in compliance with the Elastic License
# 2.0.

import re
from wcmatch import glob


class IndexingRules:
    def filter_size(self, file_details, symbol, pattern):
        """This method is used to find if the file size is matching with the pattern
            :param file_details: dictionary containing file properties
            :param symbol: >,<,>=,<=,!,!=,=,== symbol
            :param pattern: numeric part of pattern as a string
            :returns: True or False denoting whether the file size is according to the pattern
        """
        file_size = file_details['file_size']
        operation = {
            '>': file_size > int(pattern),
            '>=': file_size >= int(pattern),
            '<': file_size < int(pattern),
            '<=': file_size <= int(pattern),
            '!': file_size != int(pattern),
            '!=': file_size != int(pattern),
            '=': file_size == int(pattern),
            '==': file_size == int(pattern),
        }
        return operation.get(symbol)

    def apply_rules(self, file_details, include, exclude):
        """This method is used to check if the current file is following the indexing rule or not
            :param file_details: dictionary containing file properties
            :param include: include pattern provided for matching
            :param exclude: exlcude pattern for matching
            :returns: True or False denoting if the file is to following the indexing rule or not
        """
        result = True
        if include:
            for filtertype, pattern in include.items():
                result = self.filter_pattern(filtertype, pattern, file_details, 'include')
                if result is False:
                    return False
        if exclude:
            for filtertype, pattern in exclude.items():
                for value in (pattern or []):
                    if include and (value in (include.get(filtertype) or [])):
                        pattern.remove(value)
                result = self.filter_pattern(filtertype, pattern, file_details, 'exclude')
                if result is False:
                    return False
        return result

    def filter_pattern(self, filtertype, pattern, file_details, pattern_type):
        """This method is used to connect with network drive.
            :filtertype: denotes the type of filter used: size/path_template
            :param pattern: include/ exclude pattern provided for matching
            :param file_details: dictionary containing file properties
            :param pattern_type: include/exlcude
        """
        for value in (pattern or []):
            if filtertype == 'size':
                initial = re.match('[>,<,=,!]=?', value)
                result = self.filter_size(file_details, initial[0], re.findall("[0-9]+", value)[0])
            else:
                result = glob.globmatch(file_details['file_path'], value, flags=glob.GLOBSTAR)
            if (pattern_type == 'include' and not(result)) or (pattern_type == 'exclude' and result):
                return False
        return True
