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

from six import integer_types, string_types, binary_type



class SKLegacyExport(object):

    # Reserved properties based upon expected top-level measurement keys in JSON file
    properties  =   [   ('app_version_code',        None),
                        ('app_version_name',        None),
                        ('datetime',                None),
                        ('enterprise_id',           None),
                        ('schedule_config_version', None),
                        ('sim_operator_code',       None),
                        ('submission_type',         None),
                        ('timestamp',               None),
                        ('timezone',                None),
                        ('conditions',              [ ] ),
                        ('metrics',                 [ ] ),
                        ('requested_tests',         [ ] ),
                        ('tests',                   [ ] )
                    ]

    defaults    =   [   ('device_id',               None),
                        ('device_imei',             None),
                        ('provider_id',             None),
                        ('provider_name',           None),
                        ('measurement_method_code', 1   ),
                        ('measurement_app_name',    'FCC Speed Test app')
                    ]

    test_ids    =   {   'target':   'CLOSESTTARGET',
                        'download': 'JHTTPGETMT',
                        'upload':   'JHTTPPOSTMT',
                        'latency':  'JUDPLATENCY'   }

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


    def get_value_by_timestamp(self, event_dict, timestamp=None, default=None):
        """
        Returns value from object dictionary by matching (or nearest to) timestamp, else default
        """
        from six import integer_types, string_types

        if not isinstance(event_dict, dict):
            raise TypeError('event_dict argument must be a dictionary:%s' % type(event_dict))

        if timestamp is None:
            # Default timestamp is first timestamp in download_tests events or instance timestamp
            timestamp   =   next((odict['timestamp'] for odict in self.download_tests), self.timestamp)

        if not isinstance(timestamp, integer_types):
            self.logger.debug(  'timestamp is not an int:%s (value:%s)', type(timestamp), timestamp)
            timestamp = int(timestamp)

        timestamps      =   [ t for t in sorted(event_dict.keys(), key=lambda x: abs(timestamp - x)) ]

        if not timestamps:
            self.logger.debug(  'no value detected, returning default:%s (calling function:%s)',
                                default, inspect.stack()[1][3]  )
            return default

        if timestamp not in timestamps:
            self.logger.debug(  'no such timestamp:%s in timestamps:%s, selecting closest timestamp (calling function:%s)',
                                timestamp, timestamps, inspect.stack()[1][3] )
            timestamp   =   next((t for t in timestamps), None)

        return event_dict.get(timestamp) or default


    def get_provider_tuple(self, code=None, provider_id=None):
        """
        Returns tuple of (provider_id, provider_name) from providers dataframe matching 'sim_operator_code' value from measurements
        """
        import pandas as pd
        from six import integer_types, string_types

        if not isinstance(code, integer_types):
            code = int(self.sim_operator_code)

        if provider_id in list(self.pdf.provider_id.values):
            pdf = self.pdf[self.pdf.provider_id==provider_id]
        elif code in list(self.pdf.sim_operator_code.values):
            pdf = self.pdf[self.pdf.sim_operator_code==code]
        else:
            self.logger.warn('cannot find provider in providers data from provider_id:%s code:%s', provider_id, code)
            pdf = pd.DataFrame(columns=self.pdf.columns)
        return next(((pid, pname) for pid, pname in pdf[['provider_id', 'provider_name']].values), (None, None))


    def get_lat_long_tuple(self, timestamp=None):
        """
        Returns tuple of (latitude, longitude) from cell location metrics matching timestamp
        """
        return self.get_value_by_timestamp(self.lat_long_dict, timestamp=timestamp, default=(None, None))


    def get_phone_type_tuple(self, timestamp=None):
        """
        Returns tuple of (phone_type, phone_type_code) from network data metrics matching timestamp
        """
        return self.get_value_by_timestamp(self.phone_type_dict, timestamp=None, default=(None, None))


    # Methods returning columnar values for dataframe

    def get_latitude(self, timestamp=None):
        """
        Returns 'latitude' value from cell location metrics matching timestamp
        """
        return self.get_lat_long_tuple(timestamp=timestamp)[0]


    def get_longitude(self, timestamp=None):
        """
        Returns 'longitude' value from cell location metrics matching timestamp
        """
        return self.get_lat_long_tuple(timestamp=timestamp)[1]


    def get_timestamp(self, timestamp=None):
        """
        Returns 'datetime' value from download tests matching timestamp
        """
        return self.get_value_by_timestamp(self.datetime_dict, timestamp=timestamp)


    def get_signal_strength(self, timestamp=None):
        """
        Returns converted 'dbm' or 'signal_strength' value from cell location metrics matching timestamp
        """
        return self.get_value_by_timestamp(self.signal_strength_dict, timestamp=timestamp, default=0)


    def get_download_speed(self, timestamp=None):
        """
        Returns converted 'bytes_sec' value from download tests matching timestamp
        """
        return self.get_value_by_timestamp(self.download_speed_dict, timestamp=timestamp, default=0)


    def get_latency(self, timestamp=None):
        """
        Returns converted 'rtt_avg' value from latency tests matching timestamp
        """
        return int(self.get_value_by_timestamp(self.latency_dict, timestamp=timestamp, default=0))


    def get_provider_id(self, **kwargs):
        """
        Returns detected 'provider_id' value from providers dataframe matching 'sim_operator_code' value from measurements
        """
        if self.provider_id:
            return self.provider_id
        else:
            return self.get_provider_tuple(code=self.sim_operator_code)[0]


    def get_provider_name(self, provider_id=None, **kwargs):
        """
        Returns detected 'provider_name' value from providers dataframe matching 'sim_operator_code' value from measurements
        """
        if self.provider_name:
            return self.provider_name
        else:
            return self.get_provider_tuple(code=self.sim_operator_code, provider_id=provider_id)[1]


    def get_device_id(self, timestamp=None):
        """
        Returns detected 'device_id' value from handsets dataframe matching 'sim_operator_code' value from measurements
        """
        if self.device_id:
            return self.device_id
        else:
            hdf         =   self.hdf
            make, model =   self.handset_tuple
            provider_id =   self.get_provider_id()

            smregex     =   r'(?i)^(?:SM|SGH)-(?P<model>.+)$'

            if make.lower() == 'apple':
                code    =   str(self.phone_type_tuple[1]).lower()
                model   =   next((model for model in hdf[hdf.device_code.str.lower()==code].device_marketing_name.values), model)
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


    def get_measurement_server_location(self, timestamp=None):
        """
        Returns combined 'target' and 'target_ipaddress' values from download tests matching timestamp
        """
        return self.get_value_by_timestamp(self.target_dict, timestamp=timestamp, default='N/A')


    def get_odict(self, array, filter):
        """
        Returns first object dictionary from array matching filter
        """
        return next((odict for odict in self.get_odicts(array, filter)), {})


    def get_odicts(self, array, filter=None):
        """
        Returns all object dictionaries from array matching filter
        """
        return [ odict for odict in array if ( (filter is None) or ( filter(odict) if callable(filter) else odict.get('type') == filter) ) ]


    def get_events(self, array, filter=None):
        """
        Returns all event tuples of (timestamp, type) from array matching filter
        """
        return sorted( [    ( odict['timestamp'], odict['type'] ) for odict in array
                            if ((filter is None) or
                                (filter(odict) if callable(filter) else odict.get('type') == filter) )  ],
                        key=lambda x: x[0] )


    def get_events_dict(self, array, filter=None):
        """
        Returns event dictionary grouping events by timestamp from array matching filter
        """
        from itertools import groupby

        return { key: [ val for _, val in vlist ] for key, vlist in groupby(self.get_events(array, filter),
                                                                            key=lambda x: x[0] ) }


    def to_dataframe(self):
        """
        Returns pandas dataframe for each download_test_events entry
        """
        import pandas as pd

        columns =   [   'latitude', 'longitude', 'timestamp', 'signal_strength', 'download_speed', 'latency',
                        'provider_id', 'provider_name', 'device_id', 'device_imei', 'measurement_method_code',
                        'measurement_app_name', 'measurement_server_location'   ]

        array = []
        if self.download_test_events:
            events  =   self.download_test_events
        elif self.test_ids['download'] in self.requested_tests:
            events  =   self.target_test_events
        else:
            events  =   []

        for timestamp in events:
            row = []
            for column in columns:
                func = getattr(self, 'get_{}'.format(column))
                row.append(func(timestamp=timestamp))
            array.append(row)

        return pd.DataFrame(array, columns=columns).round( {
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


    # Properties


    @property
    def location_metrics(self):
        return self.get_odicts(array=self.metrics, filter='location')


    @property
    def network_data_metrics(self):
        return self.get_odicts(array=self.metrics, filter='network_data')


    @property
    def cell_location_metrics(self):
        return  [   odict for odicts in [
                        self.get_odicts(array=self.metrics, filter='cdma_cell_location'),
                        self.get_odicts(array=self.metrics, filter='gsm_cell_location')
                    ] for odict in odicts   ]


    @property
    def phone_identity_metric(self):
        return self.get_odict(array=self.metrics, filter='phone_identity')


    @property
    def test_types(self):
        return [ odict.get('type') for odict in self.tests ]


    @property
    def metric_types(self):
        return [ odict.get('type') for odict in self.metrics ]


    @property
    def lat_long_dict(self):
        return { odict['timestamp']: ( odict['latitude'], odict['longitude'] ) for odict in self.location_metrics }


    @property
    def phone_type_dict(self):
        return { odict['timestamp']: ( odict['phone_type'], odict['phone_type_code'] ) for odict in self.network_data_metrics }


    @property
    def signal_strength_dict(self):
        from six import integer_types, string_types
        def _convert_asu(val):
            if isinstance(val, integer_types):
                return ((2 * val) - 114)
            return val

        return { odict['timestamp']: odict.get('dbm', _convert_asu(odict.get('signal_strength')))
                    for odict in self.cell_location_metrics     }


    @property
    def download_speed_dict(self):
        from six import integer_types, string_types
        def _convert_bps(val):
            if isinstance(val, integer_types):
                return (0.000008 * val)
            return val

        return { odict['timestamp']: _convert_bps(odict.get('bytes_sec')) for odict in self.download_tests }


    @property
    def latency_dict(self):
        from six import integer_types, string_types
        def _convert_us(val):
            if isinstance(val, integer_types):
                return int(0.001 * val)
            return val

        return { odict['timestamp']: _convert_us(odict.get('rtt_avg')) for odict in self.latency_tests }


    @property
    def datetime_dict(self):
        return { odict['timestamp']: odict['datetime'] for odict in self.all_tests }


    @property
    def target_dict(self):
        def _format_target(odict):
            arr =   [ x for x in [  odict.get('target', odict.get('closest_target')),
                                    odict.get('target_ipaddress', odict.get('ip_closest_target')) ]
                        if isinstance(x, string_types) and x != '-' ]
            return ' / '.join(arr) if arr else None
        return {    odict['timestamp']: _format_target(odict) for odict in self.all_tests }


    @property
    def handset_tuple(self):
        return ( self.phone_identity_metric['manufacturer'], self.phone_identity_metric['model'] )


    @property
    def phone_type_tuple(self):
        return self.get_value_by_timestamp(self.phone_type_dict, default=(None, None))


    @property
    def all_tests(self):
        return self.get_odicts(array=self.tests)


    @property
    def target_tests(self):
        return self.get_odicts(array=self.tests, filter=self.test_ids['target'])


    @property
    def download_tests(self):
        return self.get_odicts( array=self.tests,
                                filter=lambda x: (x.get('type') == self.test_ids['download']) and (x.get('success') == True) )


    @property
    def upload_tests(self):
        return self.get_odicts( array=self.tests,
                                filter=lambda x: (x.get('type') == self.test_ids['upload']) and (x.get('success') == True) )


    @property
    def latency_tests(self):
        return self.get_odicts( array=self.tests,
                                filter=lambda x: (x.get('type') == self.test_ids['latency']) and (x.get('success') == True) )


    @property
    def metric_events_dict(self):
        return self.get_events_dict(array='metrics')


    @property
    def test_events_dict(self):
        return self.get_events_dict(array='tests')


    @property
    def location_events(self):
        return self.get_events_dict(array=self.metrics, filter='location').keys()


    @property
    def target_test_events(self):
        return self.get_events_dict(array=self.tests, filter=self.test_ids['target']).keys()


    @property
    def download_test_events(self):
        return self.get_events_dict(array=self.tests, filter=self.test_ids['download']).keys()


    @property
    def upload_test_events(self):
        return self.get_events_dict(array=self.tests, filter=self.test_ids['upload']).keys()


    @property
    def latency_test_events(self):
        return self.get_events_dict(array=self.tests, filter=self.test_ids['latency']).keys()


#
