# -*- coding: utf-8 -*-

import os
import sys
import json
import logging

import pandas as pd

import mba2mfii
from mba2mfii.tools import json_decode

from itertools import groupby
from time import strftime



class MBAExport:
    
    # Reserved properties based upon expected top-level keys in JSON file
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
    
    def __init__(self, fp, **kwargs):
        """
        """
        self.logger = logging.getLogger(__name__)
        self.pdf    =   mba2mfii.data['providers']
        self.hdf    =   mba2mfii.data['handsets']
        
        if isinstance(fp, str):
            if not os.path.isfile(fp):
                raise TypeError('invalid file pointer: {0!r}'.format(fp))
            else:
                fp = open(fp, 'r')
        
        if not hasattr(fp, 'read'):
            raise TypeError('invalid file pointer: {0!r}'.format(fp))
        
        if isinstance(fp.read(0), bytes):
            raise TypeError('invalid file pointer: {0!r} (binary mode detected)'.format(fp))
        
        self.logger.debug('loading file: {0!r}'.format(fp))
        self.json_data = json.load(fp, object_hook=json_decode)
        
        if isinstance(self.json_data, dict):
            self.json_data = [ self.json_data ]
        
        if len(self.json_data) > 1:
            self.logger.warn('multiple submissions detected')
        
        # Initialize properties for each top-level key defined in properties
        for key, val in self.properties:
            self.__dict__[key] = self.data.get(key, val)
        
        # Initialize properties for each default defined in defaults
        for key, val in self.defaults:
            self.__dict__[key] = kwargs.get(key, val)
        
        # Set provider_name if provider_id specified
        self.provider_name = self.get_provider_name(provider_id=self.provider_id)
    
    
    def get_provider_tuple(self, code=None, provider_id=None):
        """
        """
        if not isinstance(code, int):
            code = int(self.sim_operator_code)
        
        if provider_id in list(self.pdf.provider_id.values):
            pdf = self.pdf[self.pdf.provider_id==provider_id]
        elif code in list(self.pdf.sim_operator_code.values):
            pdf = self.pdf[self.pdf.sim_operator_code==code]
        else:
            self.logger.warn('cannot find provider in providers data from provider_id:%s code:%s', provider_id, code)
            pdf = pd.DataFrame(columns=self.pdf.columns)
        return next(((pid, pname) for pid, pname in pdf[['provider_id', 'provider_name']].values), (None, None))
    
    
    def get_value_by_timestamp(self, event_dict, timestamp=None, default=None):
        """
        """
        if not isinstance(event_dict, dict):
            raise TypeError('event_dict argument must be a dictionary: %s' % type(event_dict))
        
        if timestamp is None:
            # Default timestamp is first timestamp in download_tests events or instance timestamp
            timestamp   =   next((odict['timestamp'] for odict in self.download_tests), self.timestamp)
        
        if not isinstance(timestamp, int):
            self.logger.debug(  'timestamp is not an int:%s (value:%s)', type(timestamp), timestamp)
            timestamp = int(timestamp)
        
        timestamps      =   [ t for t in sorted(event_dict.keys(), key=lambda x: abs(timestamp - x)) ]
        
        if timestamp not in timestamps:
            self.logger.debug(  'cannot find match for timestamp:%s in timestamps:%s, selecting next closest timestamp',
                                timestamp, timestamps )
            timestamp   =   next((t for t in timestamps), None)
        
        return event_dict.get(timestamp, default)
    
    
    def get_lat_long(self, timestamp=None):
        """
        """
        return self.get_value_by_timestamp(self.lat_long_dict, timestamp=timestamp, default=(None, None))
    
    
    def get_latitude(self, timestamp=None):
        return self.get_lat_long(timestamp=timestamp)[0]
    
    
    def get_longitude(self, timestamp=None):
        return self.get_lat_long(timestamp=timestamp)[1]
    
    
    def get_timestamp(self, timestamp=None):
        return self.get_value_by_timestamp(self.datetime_dict, timestamp=timestamp)
    
    
    def get_signal_strength(self, timestamp=None):
        """
        """
        return self.get_value_by_timestamp(self.signal_strength_dict, timestamp=timestamp)
    
    
    def get_download_speed(self, timestamp=None):
        """
        """
        return self.get_value_by_timestamp(self.download_speed_dict, timestamp=timestamp)
    
    
    def get_latency(self, timestamp=None):
        """
        """
        return int(self.get_value_by_timestamp(self.latency_dict, timestamp=timestamp, default=0))
    
    
    def get_provider_id(self, timestamp=None):
        """
        """
        if self.provider_id:
            return self.provider_id
        else:
            return self.get_provider_tuple(code=self.sim_operator_code)[0]
    
    
    def get_provider_name(self, timestamp=None, provider_id=None):
        """
        """
        if self.provider_name:
            return self.provider_name
        else:
            return self.get_provider_tuple(code=self.sim_operator_code, provider_id=provider_id)[1]
    
    
    def get_device_id(self, timestamp=None):
        """
        """
        if self.device_id:
            return self.device_id
        else:
            device_id = None
            
            hdf = self.hdf[self.hdf.provider_id==self.get_provider_id()]
            manufacturer, model = self.handset_tuple
            if manufacturer.lower() == 'apple' and model.lower() == 'iphone 3g':
                # Special case for newer iOS devices that report as "iPhone 3G"
                code = self.get_value_by_timestamp(self.phone_type_dict, timestamp=timestamp)[1]
                device_id = next((id for id in hdf[hdf.device_code.str.lower()==code.lower()].device_id.values), None)
            elif model.lower() in list(hdf.device_marketing_name.str.lower()):
                device_id = next((id for id in hdf[hdf.device_marketing_name.str.lower()==model.lower()].device_id.values), None)
                self.logger.debug(  'found exact device match for handset:%s -- returning id:%s',
                                    self.handset_tuple, id  )
            elif manufacturer.lower() in list(hdf.device_manufacturer.str.lower()):
                hdf = hdf[hdf.device_manufacturer.str.lower()==manufacturer.lower()]
                self.logger.info(   'found manufacturer match for handset:%s -- possible devices:%s',
                                    self.handset_tuple, list(hdf.device_marketing_name.values)  )
            else:
                self.logger.warn(   'cannot find manufacturer or device model for handset:%s (provider ID:%s)',
                                    self.handset_tuple, self.get_provider_id()  )
            return device_id
        
    
    
    def get_device_imei(self, timestamp=None):
        """
        """
        return self.device_imei
    
    
    def get_measurement_method_code(self, timestamp=None):
        """
        """
        return self.measurement_method_code
    
    
    def get_measurement_app_name(self, timestamp=None):
        """
        """
        return self.measurement_app_name
    
    
    def get_measurement_server_location(self, timestamp=None):
        """
        """
        return self.get_value_by_timestamp(self.target_dict, timestamp=timestamp)
    
    
    def get_odict(self, array, filter):
        """
        """
        return next((odict for odict in self.get_odicts(array, filter)), {})
    
    
    def get_odicts(self, array, filter=None):
        """
        """
        return [ odict for odict in array if ( (filter is None) or (odict.get('type') == filter) ) ]
    
    
    def get_events(self, array, filter=None):
        return sorted( [    ( odict['timestamp'], odict['type'] ) for odict in array
                            if (filter is None) or (odict.get('type') == filter)  ],
                        key=lambda x: x[0] )
    
    
    def get_events_dict(self, array, filter=None):
        return { key: [ val for _, val in vlist ] for key, vlist in groupby( self.get_events(array, filter), key=lambda x: x[0] ) }
    
    
    def to_dataframe(self):
        """
        """
        columns =   [   'latitude', 'longitude', 'timestamp', 'signal_strength', 'download_speed', 'latency',
                        'provider_id', 'provider_name', 'device_id', 'device_imei', 'measurement_method_code',
                        'measurement_app_name', 'measurement_server_location'   ]
        
        array = []
        for timestamp in self.download_test_events:
            row = []
            for column in columns:
                func = getattr(self, 'get_{}'.format(column))
                row.append(func(timestamp=timestamp))
            array.append(row)
        
        return pd.DataFrame(array, columns=columns)        
    
    
    def to_csv(self, filename):
        """
        """
        try:
            os.makedirs(os.path.dirname(filename))
        except:
            pass
        
        df = self.to_dataframe()
        df.to_csv(filename, index=False)
        
    
    @property
    def data(self):
        return next((data for data in self.json_data), dict())
    
    
    @property
    def location_metrics(self):
        return self.get_odicts(array=self.metrics, filter='location')
    
    
    @property
    def lat_long_dict(self):
        return { odict['timestamp']: ( odict['latitude'], odict['longitude'] ) for odict in self.location_metrics }
    
    
    @property
    def phone_type_dict(self):
        return { odict['timestamp']: ( odict['phone_type'], odict['phone_type_code'] ) for odict in self.network_data_metrics }
    
    
    @property
    def network_data_metrics(self):
        return self.get_odicts(array=self.metrics, filter='network_data')
    
    
    @property
    def cell_location_metrics(self):
        return [    *self.get_odicts(array=self.metrics, filter='cdma_cell_location'),
                    *self.get_odicts(array=self.metrics, filter='gsm_cell_location')    ]
    
    
    @property
    def signal_strength_dict(self):
        def _convert_asu(val):
            if isinstance(val, int):
                return ((2 * val) - 114)
            return val
        
        return { odict['timestamp']: odict.get('dbm', _convert_asu(odict.get('signal_strength')))
                    for odict in self.cell_location_metrics     }
    
    
    @property
    def download_speed_dict(self):
        def _convert_bps(val):
            if isinstance(val, int):
                return (0.000008 * val)
            return val
        
        return { odict['timestamp']: _convert_bps(odict.get('bytes_sec')) for odict in self.download_tests }
    
    
    @property
    def latency_dict(self):
        def _convert_us(val):
            if isinstance(val, int):
                return int(0.001 * val)
            return val
        
        return { odict['timestamp']: _convert_us(odict.get('rtt_avg')) for odict in self.latency_tests }
    
    
    @property
    def datetime_dict(self):
        return { odict['timestamp']: odict['datetime'] for odict in self.download_tests }
    
    
    @property
    def target_dict(self):
        return { odict['timestamp']: '{} / {}'.format(odict['target'], odict['target_ipaddress']) for odict in self.download_tests }
    
    
    @property
    def test_types(self):
        return [ odict.get('type') for odict in self.tests ]
    
    
    @property
    def metric_types(self):
        return [ odict.get('type') for odict in self.metrics ]
    
    
    @property
    def phone_identity(self):
        return self.get_odict(array=self.metrics, filter='phone_identity')
    
    
    @property
    def handset_tuple(self):
        return ( self.phone_identity['manufacturer'], self.phone_identity['model'] )
    
    
    @property
    def download_tests(self):
        return self.get_odicts(array=self.tests, filter='JHTTPGETMT')
    
    
    @property
    def upload_tests(self):
        return self.get_odicts(array=self.tests, filter='JHTTPPOSTMT')
    
    
    @property
    def latency_tests(self):
        return self.get_odicts(array=self.tests, filter='JUDPLATENCY')
    
    
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
    def download_test_events(self):
        return self.get_events_dict(array=self.tests, filter='JHTTPGETMT').keys()



#