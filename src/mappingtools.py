#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = """Co-Pierre Georg (co-pierre.georg@uct.ac.za)"""

import sys
import logging
import re

from math import sqrt

from fuzzywuzzy import process
from fuzzywuzzy import fuzz

from src.dirtystringtools import DirtyString


#-------------------------------------------------------------------------
#
#  class Mapping
#
#-------------------------------------------------------------------------
class Mapping(object):
    __version__ = 0.9


#
# VARIABLES
#
    identifier = ""
    from_strings = []  # contains the raw from_strings
    reduced_from_strings = {}  # contains the reduced from_strings with unique entries and relative frequencies
    mapping_original_standardized_from_strings = {}  # contains the original string as key and the corresponding standardized string as value

    # NOTE: this variable is not always needed, e.g. when there is only one input file but with multiple
    #       occurences of certain strings. in this case the mapping is not between files, but from the various
    #       forms a given string is written to it's unique (correct) form
    to_string_array = []  # contains the raw to_strings
    to_string_dict = {}  # contains the reduced to_strings with unique entries and relative frequencies


#
#  METHODS
#
    #-------------------------------------------------------------------------
    #  __init__
    #-------------------------------------------------------------------------
    def __init__(self):
        pass
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    #
    #-------------------------------------------------------------------------
    def tuple_to_string(self, tuple):
        """
        Takes a tuple and transforms it into a string

        Args:
            tuple (tuple)

        Returns:
            result (str) -- the string corresponding to the tuple with "_" between two entries of the tuple
        """

        result = ""
        for token in tuple:
            result += token + "_"
        return result.rstrip("_")
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    #
    #-------------------------------------------------------------------------
    def read_redundant_strings(self, redundant_strings_file_name):
        """
        This file reads redundant strings into an array

        Args:
            redundant_strings_file_name (str)

        Returns:
            redundant_strings (list)
        """

        redundant_strings = []

        # read redundant strings from file.
        redundant_strings_file = open(redundant_strings_file_name, 'r')
        for line in redundant_strings_file.readlines():
            redundant_strings.append(line.strip())
            # we also remove the upper case version of each string
            redundant_strings.append(line.strip().upper())
        redundant_strings_file.close()

        return redundant_strings
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # standardize_string(
    #   string,
    #   redundant_strings_file_name
    #   )
    #-------------------------------------------------------------------------
    def standardize_string(self,
                           original_string,
                           redundant_strings
    ):
        """
        Takes an original string and standardizes it by stripping special characters and redundant strings

        Args:
            original_string (str) -- string to be standardized
            redundant_strings_file_name (str) -- the file where redundant strings (one per line) are listed

        Returns:
            standardized_string (str) -- standardized string without special characters and redundant strings

        Note:
        - The redundant_strings_file contains strings that can be stripped from the strings that are being parsed.
          Examples: 'the', 'of'
        - Each string in the redundant_strings_file is in a single line
        - The uppercase version of each redundant string is also automatically removed

        """
        dirtystring = DirtyString()

        original_string = dirtystring.standardize(original_string.upper())
        original_string = dirtystring.normalize(original_string)
        #original_string = dirtystring.translit_nordic(original_string)  # TODO: for some reason this throws UniDecodeError sometimes

        # remove redundant strings
        for redundant_string in redundant_strings:
            redundant_string = dirtystring.standardize(redundant_string)  # this assumes that the to and from strings
            redundant_string = dirtystring.normalize(redundant_string)    # are also standardized
            original_string = re.sub(redundant_string, '', original_string)

        return original_string
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # compute_string_frequency(
    #   string_array,
    #   )
    #-------------------------------------------------------------------------
    def compute_string_frequency(self,
                                 string_array
    ):
        """
        Computes the absolute frequency of every string in a string_array

        Args:
            string_array (list) -- array containing strings, possibly more than once

        Returns:
            reduced_string_dict (dict) -- dict containing unique string as key and frequency as value

        Note:
            - Absolute frequency is the number of occurences of a unique string
            - This method takes any hashable object and computes the frequency, including tuples

        """

        reduced_string_dict = {}

        for entry in string_array:
            if entry in reduced_string_dict:
                reduced_string_dict[entry] += 1
            else:
                reduced_string_dict[entry] = 1

        return reduced_string_dict
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # find_best_match(
    #   matching_string,
    #   original_strings,
    #   number_of_fuzzy_options,
    #   threshold_fuzziness
    #   )
    #-------------------------------------------------------------------------
    def find_best_match_between_files(self,
                        from_dict_entry,
                        to_dict,
                        number_of_fuzzy_options,
                        threshold_fuzziness,
                        use_frequency=None,
                        debug=None
    ):
        """
        Finds the best match of a from_string in an array of to_strings

        Args:
            from_dict_entry (str) -- the {string: frequency} that is to be matched
            to_dict (dict) -- the dict of {strings: frequency} from which the best match is to be found
            number_of_fuzzy_options (int) -- the number of alternatives of the matching_string fuzzywuzzy should find in the original_strings
            threshold_fuzziness (int) -- the lower threshold for the precision of fuzzy matches

        Returns:
            best_match (str) -- the best match to matching_string in original_strings

        Note:


        """
        to_strings = list(to_dict.keys())


        # find fuzzy matches in the reduced list of all entries
        matching_options = process.extract(
            from_dict_entry[0],
            to_strings,  # we need the list of to_strings here only, the frequencies are used later
            limit=number_of_fuzzy_options
        )

        # we start with the original string
        best_match = from_dict_entry[0]  # if we don't find a better match, return original string
        best_match_precision = 0.0  # original string is not in the reduced list of all entries
        best_match_fuzziness = 0
        original_frequency = int(from_dict_entry[1])

        # the best matching option is found by checking fuzziness and relative frequency of all matches
        for matching_option in matching_options:
            match_fuzziness = matching_option[1]
            match_frequency = to_dict[matching_option[0]]

            # we replace a name with a similar name only if the similar name
            # has a higher frequency; we also check that we only consider
            # reasonable matches, otherwise we might match with a fairly
            # different, but very prominent name
            matching_precision = match_fuzziness/100.0*match_frequency - original_frequency

            # finally, do the comparison by finding best match and checking that fuzziness is above some threshold
            if use_frequency:  # in this case matching is done on precision, while only controlling for fuzziness
                if matching_precision > best_match_precision and match_fuzziness > threshold_fuzziness:
                    best_match_precision = matching_precision
                    best_match = matching_option[0]
            else:  # in this case matching is done based on fuzziness
                if match_fuzziness > best_match_fuzziness and match_fuzziness > threshold_fuzziness:
                    best_match_fuzziness = match_fuzziness
                    best_match = matching_option[0]

            if debug and use_frequency:  # debug
                print from_dict_entry[0] + "[" + str(original_frequency) + "] vs.", matching_option, "-->", best_match, best_match_precision
            if debug and not use_frequency:
                print from_dict_entry[0], "vs.", matching_option, "-->", best_match, best_match_fuzziness

            if not use_frequency:  # if we don't use the precision, return best_match_fuzziness
                best_match_precision = best_match_fuzziness

        return [best_match, best_match_precision]
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # find_best_match_tuple(
    #   matching_string,
    #   original_strings,
    #   number_of_fuzzy_options,
    #   threshold_fuzziness
    #   )
    #-------------------------------------------------------------------------
    def find_best_match_tuple(self,
                        matching_tuple,
                        original_tuples,
                        threshold_fuzziness,
                        matching_scaling_factor,
                        debug=None
    ):
        """
        Finds the best match of a string tuple in an array of string tuples

        Args:
            matching_string (tuple) -- the tuple that is to be matched
            original_strings (list) -- the list of tuples from which the best match is to be found
            number_of_fuzzy_options (int) -- the number of alternatives of the matching_string fuzzywuzzy should find in the original_strings
            threshold_fuzziness (int) -- the lower threshold for the precision of fuzzy matches

        Returns:
            best_match (str) -- the best match to matching_string in original_strings

        Note:
            This method finds an element-wise best match for every element in the tuple and then constructs the overall best match

        """
        best_distance = -10000000000.0  # a very large negative number so it is easy to beat by an entry in the original_tuples

        # the possible matches are the original_strings array reduced by the
        # string we are trying to match
        reduced_original_tuples = list(original_tuples)
        reduced_original_tuples.remove(matching_tuple)

        matching_frequency = original_tuples[matching_tuple]  # frequency of the matching tuple
        best_match = matching_tuple  # if we don't find any match, the original token is the best match

        matching_string = self.tuple_to_string(matching_tuple)  # construct a string from a token

        # loop over all remaining tuples and compute geometric distance
        for original_tuple in reduced_original_tuples:
            # make sure each entry has the same length as the matching_tuple
            if len(matching_tuple) != len(original_tuple):
                print "<< E: tuple length does not match: ", matching_tuple, original_tuple
                break

            # compute the frequency of the entire tuple (not the individual entries)
            entry_frequency = original_tuples[original_tuple]

            # go over each entry
            sum = 0.0  # the string distance between two tuples
            for i in range(0, len(original_tuple)):
                # compute the fuzz ratio of each entry
                entry_fuzz_ratio = fuzz.ratio(matching_tuple[i], original_tuple[i])
                # fuzzy ratio times entry frequency
                sum += (100 - entry_fuzz_ratio)*(100 - entry_fuzz_ratio)

            # the distance is computed as geometric distance of token distances, taking into account relative frequencies
            # the scaling factor determines the condition when to choose a worse-matching tuple that is much more
            # frequent
            distance = matching_scaling_factor*entry_frequency - matching_frequency*sqrt(sum)

            # to prevent always going with the most common tuple, we also compute the fuzzy distance between the string
            # versions of the tuples.
            original_string = self.tuple_to_string(original_tuple)
            fuzzy_distance = fuzz.ratio(matching_string, original_string)

            if distance > best_distance and fuzzy_distance > threshold_fuzziness:  # we have a new best match
                best_distance = distance
                best_match = original_tuple

            if debug:  # debug
                print matching_tuple, original_tuple, matching_frequency, entry_frequency, best_match, best_distance

        return [best_match, best_distance]
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # write_reduced_from_strings(out_file_name)
    #-------------------------------------------------------------------------
    def write_reduced_from_strings(self, out_file_name):
        """
        Writes the reduced from string array to out_file

        Args:
            out_file_name (str) -- the name of the output file

        Returns:

        Note:

        """
        out_file = open(out_file_name, 'w')
        out_text = ""

        for key in self.reduced_from_strings.keys():
            out_text += key+ ";" + str(self.reduced_from_strings[key]) + "\n"

        out_file.write(out_text)
        out_file.close()
    #-------------------------------------------------------------------------