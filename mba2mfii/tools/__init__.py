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
    Override default JSON decoder to recursively convert strings into numeric or boolean
    """
    from six import string_types
    from decimal import InvalidOperation, Decimal as decimal
    from distutils.util import strtobool

    str_converters  =   [   ( lambda x: int(x) if (int(x) == decimal(x)) else decimal(x), (ValueError, InvalidOperation) ),
                            ( lambda x: decimal(x), (ValueError, InvalidOperation) ),
                            ( lambda x: bool(strtobool(x)), ValueError ) ]

    if isinstance(obj, string_types):
        for converter, error in str_converters:
            if not callable(converter):
                continue
            try:
                return converter(obj)
            except error:
                pass
        return obj
    elif isinstance(obj, (float, decimal)) and (int(obj) == decimal(obj)):
        return int(obj)
    elif isinstance(obj, dict):
        return { k: json_decode(v) for k, v in obj.items() }
    elif isinstance(obj, list):
        return [ json_decode(v) for v in obj ]
    else:
        return obj


#
