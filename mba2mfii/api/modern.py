# -*- coding: utf-8 -*-

import os
import sys
import json
import logging

import inspect

import warnings
warnings.filterwarnings('ignore', message='numpy.dtype size changed')
warnings.filterwarnings('ignore', message='numpy.ufunc size changed')

import pandas as pd

import mba2mfii
from mba2mfii.tools import json_decode

from re import match, sub

from itertools import groupby
from time import strftime

from six import integer_types, string_types, iteritems

#

class SKModernExport(object):
    #
    # Reserved properties based upon expected top-level measurement keys in JSON file
    properties  =   [   ('metadata',                { } ),
                        ('device_environment',      { } ),
                        ('tests',                   { } )
                    ]

    defaults    =   [   ('device_id',               None),
                        ('device_imei',             None),
                        ('provider_id',             None),
                        ('provider_name',           None),
                        ('measurement_method_code', 1   ),
                        ('measurement_app_name',    'FCC Speed Test app v2')
                    ]

    test_ids    =   {   'download': 'download',
                        'upload':   'upload',
                        'latency':  'latency'       }

    columns     =   [   'latitude', 'longitude', 'timestamp', 'signal_strength', 'download_speed', 'latency',
                        'provider_id', 'provider_name', 'device_id', 'device_imei', 'measurement_method_code',
                        'measurement_app_name', 'measurement_server_location'   ]


    def __init__(self, data, **kwargs):
        """
        """
        self.logger =   logging.getLogger(__name__)
        self.pdf    =   mba2mfii.data['providers']
        self.hdf    =   mba2mfii.data['handsets']

        try:
            assert isinstance(data, dict), 'data must be a JSON dict:%s' % data
        except AssertionError:
            self.logger.error('Must initialize {} with valid data:{}'.format(self.__class__.__name__, type(data)))
            raise

        self.data   =   data

        # Initialize properties for each top-level key defined in properties
        for key, val in self.properties:
            self.__dict__[key] = self.data.get(key, val)

        # Initialize properties for each default defined in defaults
        for key, val in self.defaults:
            self.__dict__[key] = kwargs.get(key, val)

        # Set provider_name if provider_id specified
        self.provider_name = self.get_provider_name(provider_id=self.provider_id)


    # Public instance methods

    def to_dataframe(self):
        """
        Returns pandas dataframe with test results entry
        """
        import pandas as pd

        row     =   [ ]
        for column in self.columns:
            func = getattr(self, 'get_{}'.format(column))
            row.append(func())

        array   =   [ row ]

        return pd.DataFrame(array, columns=self.columns).round( {
            'latitude':         8,
            'longitude':        8,
            'download_speed':   6   } )


    def to_csv(self, filename):
        """
        Writes pandas dataframe to CSV file
        """
        import os

        try:
            os.makedirs(os.path.dirname(filename))
        except:
            pass

        df = self.to_dataframe()
        df.to_csv(filename, index=False)


    # Private helper methods

    def _get_nested_dict(self, d, keys, default=None):
        assert type(keys) is list
        if d is None:
            return default
        if not keys:
            return d
        return self._get_nested_dict(d.get(keys[0]), keys[1:], default=default)


    def _get_handset_tuple(self):
        """
        Returns tuple of (manufacturer, model) from device environment data
        """
        return ( self._get_device_manufacturer(), self._get_device_model() )


    def _get_provider_tuple(self, carrier=None, provider_id=None):
        """
        Returns tuple of (provider_id, provider_name) from providers dataframe matching 'carrier_name' value from device environment
        """
        import pandas as pd
        from six import integer_types, string_types

        if not isinstance(carrier, string_types):
            return (None, None)

        if provider_id in list(self.pdf.provider_id.values):
            pdf = self.pdf[self.pdf.provider_id==provider_id]
        elif carrier in list(self.pdf.provider_name.values):
            pdf = self.pdf[self.pdf.provider_name==carrier]
        else:
            self.logger.warn('cannot find provider in providers data from provider_id:%s carrier:%s', provider_id, carrier)
            return (provider_id, carrier)
        return next(((pid, pname) for pid, pname in pdf[['provider_id', 'provider_name']].values), (None, None))


    def _get_device_manufacturer(self):
        """
        Returns 'manufacturer' value from device environment
        """
        keys    =   [ 'manufacturer' ]
        return self._get_nested_dict(self.device_environment, keys)


    def _get_device_model(self):
        """
        Returns 'model' value from device environment
        """
        keys    =   [ 'model' ]
        return self._get_nested_dict(self.device_environment, keys)


    def _get_device_carrier(self):
        """
        """
        keys    =   [ 'carrier_name' ]
        return self._get_nested_dict(self.device_environment, keys)


    # Converters

    def convert_asu_to_dbm(self, val):
        from six import integer_types, string_types
        if isinstance(val, integer_types):
            return ((2 * val) - 114)
        return val


    def convert_bps_to_mbps(self, val):
        from six import integer_types, string_types
        if isinstance(val, integer_types):
            return (0.000008 * val)
        return val


    def convert_microsecond_to_millisecond(self, val):
        from six import integer_types, string_types
        if isinstance(val, integer_types):
            return int(0.001 * val)
        return val


    def convert_timestamp_str(self, val):
        from six import integer_types, string_types
        from datetime import datetime
        if isinstance(val, string_types):
            return int(datetime.strptime(val, '%Y-%m-%dT%H:%M:%SZ').timestamp())
        return val


    # Methods returning columnar values for dataframe

    def get_latitude(self, **kwargs):
        """
        Returns 'latitude' value from download test environment location data
        """
        keys    =   [ 'download', 'environment', 'location', 'lat' ]
        return self._get_nested_dict(self.tests, keys)


    def get_longitude(self, **kwargs):
        """
        Returns 'longitude' value from download test environment location data
        """
        keys    =   [ 'download', 'environment', 'location', 'lon' ]
        return self._get_nested_dict(self.tests, keys)


    def get_timestamp(self, **kwargs):
        """
        Returns 'local_datetime' value from download tests
        """
        keys    =   [ 'download', 'local_datetime' ]
        return self._get_nested_dict(self.tests, keys)


    def get_signal_strength(self, **kwargs):
        """
        Returns 'cellular_strength' value from download test environment telephony data
        """
        keys    =   [ 'download', 'environment', 'telephony', 'cellular_strength' ]
        return self._get_nested_dict(self.tests, keys, default=0)


    def get_download_speed(self, **kwargs):
        """
        Returns converted 'throughput' value from download tests
        """
        keys    =   [ 'download', 'throughput' ]
        return self.convert_bps_to_mbps(self._get_nested_dict(self.successful_tests, keys, default=0))


    def get_latency(self, **kwargs):
        """
        Returns converted 'round_trip_time' value from latency tests
        """
        keys    =   [ 'latency', 'round_trip_time' ]
        return int(self.convert_microsecond_to_millisecond(self._get_nested_dict(self.successful_tests, keys, default=0)))


    def get_measurement_server_location(self, **kwargs):
        """
        Returns 'target' value from download tests
        """
        keys    =   [ 'download', 'target' ]
        return self._get_nested_dict(self.tests, keys, default='N/A')


    def get_provider_id(self, **kwargs):
        """
        Returns detected 'provider_id' value from providers dataframe matching 'sim_operator_code' value from measurements
        """
        if self.provider_id:
            return self.provider_id
        else:
            return self._get_provider_tuple(carrier=self._get_device_carrier())[0]


    def get_provider_name(self, provider_id=None, **kwargs):
        """
        Returns detected 'provider_name' value from providers dataframe matching 'sim_operator_code' value from measurements
        """
        if self.provider_name:
            return self.provider_name
        else:
            return self._get_provider_tuple(carrier=self._get_device_carrier(), provider_id=provider_id)[1]


    def get_device_id(self, **kwargs):
        """
        Returns detected 'device_id' value from handsets dataframe
        """
        if self.device_id:
            return self.device_id
        else:
            hdf         =   self.hdf
            make, model =   self.handset_tuple
            provider_id =   self.get_provider_id()

            smregex     =   r'(?i)^(?:SM|SGH)-(?P<model>.+)$'

            if make.lower() == 'apple':
                model   =   next((model for model in hdf[hdf.device_code.str.lower()==model].device_marketing_name.values), model)
            elif make.lower() == 'samsung' and match(smregex, model):
                dmodel  =   sub(smregex, '\g<model>', model).lower()
                model   =   next((model for model in hdf[hdf.device_model.str.lower()==dmodel].device_marketing_name.values), model)

            device_ids  =   list(hdf[hdf.device_marketing_name.str.lower()==model.lower()].device_id.values)
            hdf         =   hdf[hdf.provider_id==provider_id]

            if hdf[hdf.device_id.isin(device_ids)].empty:
                if len(device_ids) == 1:
                    device_id   =   next((id for id in device_ids), None)
                    self.logger.warn(   'Device ID:%s detected but not approved for Provider ID:%s (make:%s model:%s)',
                                        device_id, provider_id, make, model     )
                elif len(device_ids) > 1:
                    device_id   =   None
                    self.logger.warn(   'Multiple Device IDs:%s detected but none approved for Provider ID:%s (make:%s model:%s)',
                                        device_ids, provider_id, make, model    )
                else:
                    device_id   =   None
                    self.logger.warn(   'No devices matched for Provider ID:%s (make:%s model:%s) -- allowed Device IDs:%s',
                                        provider_id, make, model, list(hdf.device_id.values)    )
            else:
                device_ids  =   list(hdf[hdf.device_id.isin(device_ids)].device_id.values)
                if len(device_ids) == 1:
                    device_id   =   next((id for id in device_ids), None)
                    self.logger.debug(  'Device ID:%s detected and approved for Provider ID:%s (make:%s model:%s)',
                                        device_id, provider_id, make, model  )
                else:
                    device_id   =   next((id for id in device_ids), None)
                    self.logger.warn(  'Multiple Device IDs:%s detected and approved for Provider ID:%s (make:%s model:%s) -- returning Device ID:%s',
                                        device_ids, make, model, device_id  )
            return device_id


    def get_device_imei(self, timestamp=None):
        """
        Returns 'device_imei' value if specified during initialization, else default
        """
        return self.device_imei


    def get_measurement_method_code(self, timestamp=None):
        """
        Returns 'measurement_method_code' value if specified during initialization, else default
        """
        return self.measurement_method_code


    def get_measurement_app_name(self, timestamp=None):
        """
        Returns 'measurement_app_name' value if specified during initialization, else default
        """
        return self.measurement_app_name


    # Properties


    @property
    def test_types(self):
        """
        """
        return list(self.tests.keys())


    @property
    def handset_tuple(self):
        return self._get_handset_tuple()


    @property
    def successful_tests(self):
        return { obj: odict for obj, odict in iteritems(self.tests) if odict.get('successes') > 0 }



#
