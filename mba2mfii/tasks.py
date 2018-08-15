# -*- coding: utf-8 -*-

import logging
import os, sys
import traceback

import mba2mfii

import pandas as pd


class Task(object):
    
    def __init__(self):
        self.input  =   []
        self.output =   None
        
        self.args   =   {   'clobber':      False,
                            'dry_run':      False,
                            'device_imei':  None    }
        
        self.data   =   pd.DataFrame()
                
        self.logger =   logging.getLogger(__name__)    
    
    
    def build_output(self, df):
        """
        Iteratively build output by appending pandas DataFrames
        """
        import pandas as pd
        
        if not isinstance(df, pd.DataFrame):
            msg = 'argument df must be a pandas DataFrame:{}'.format(type(df))
            self.logger.error(msg)
            raise ValueError(msg)
        
        if df.empty:
            self.logger.warn('detected empty DataFrame, skipping build_output()')
        else:
            self.logger.debug('appending {} rows to output DataFrame'.format(len(df)))
            self.data = self.data.append(df, ignore_index=True)
    
    
    def write_output(self, output=None):
        """
        Write combined pandas DataFrame to output CSV
        """
        if output is None:
            output = self.output
        
        if not self.args['dry_run']:
            if not os.path.exists(os.path.dirname(output)):
                try:
                    os.makedirs(os.path.dirname(output))
                except:
                    pass
        
        if self.data.empty:
            self.logger.warn('skipping write to output file:{} -- results DataFrame empty'.format(output))
        else:
            self.logger.info('writing {} rows to output file:{}'.format(len(self.data), output))
            if os.path.exists(output) and not self.args['clobber']:
                self.logger.warn('skipping write to output file:{} -- file exists and clobber is False'.format(output))
            elif self.args['dry_run']:
                self.logger.info('skipping write to output file:{} -- dry run is True'.format(output))
            else:
                self.data.to_csv(output, index=False)



#