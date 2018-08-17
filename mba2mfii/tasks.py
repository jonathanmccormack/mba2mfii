# -*- coding: utf-8 -*-

import os, sys
import logging

import warnings
warnings.filterwarnings('ignore', message='numpy.dtype size changed')
warnings.filterwarnings('ignore', message='numpy.ufunc size changed')

import pandas as pd


class Task(object):

    def __init__(self):
        import pandas as pd
        import logging

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
            self.logger.warn('detected empty DataFrame -- skipping build_output()')
        else:
            self.logger.debug('appending {} rows to output DataFrame'.format(len(df)))
            self.data = self.data.append(df, ignore_index=True)


    def sort_output(self, sort_columns=None, ascending=True):
        """
        Sort data values by sort_columns
        """
        if self.data.empty:
            self.logger.warn(   'skipping sort of output -- results DataFrame empty' )
        else:
            if (set(sort_columns) - set(self.data.columns)):
                self.logger.error(  'skipping sort of output -- sort_columns:%s not in DataFrame columns:%s'
                                    (set(sort_columns) - set(self.data.columns)), self.data.columns     )
            else:
                self.data = self.data.sort_values(by=sort_columns, ascending=ascending)


    def write_output(self, output=None):
        """
        Write combined pandas DataFrame to output CSV
        """
        import os

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
