"""
Common tools for use throughout script
"""

import sys
import logging

logger = logging.getLogger(__name__)


def snake_case(string):
    from re import sub
    s1 = sub(r'[\W_]+', '', str(string))
    s2 = sub('(.)([A-Z][a-z]+)', r'\1_\2', s1)
    return sub('([a-z0-9])([A-Z])', r'\1_\2', s2).lower()


def symbolize(string):
    from re import sub
    return sub(r'[\W_]+', '_', sub(r'\(.*\)', '', str(string)).lower().strip())


def json_decode(obj):
    """
    Override default JSON decoder to recursively convert integer-like strings into integers
    """
    from six import string_types
    
    if isinstance(obj, string_types):
        try:
            return int(obj)
        except ValueError:
            return obj
    elif isinstance(obj, dict):
        return { k: json_decode(v) for k, v in obj.items() }
    elif isinstance(obj, list):
        return [ json_decode(v) for v in obj ]
    else:
        return obj


#