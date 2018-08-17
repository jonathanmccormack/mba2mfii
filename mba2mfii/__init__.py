# -*- coding: utf-8 -*-

import os, sys
import logging

import warnings
warnings.filterwarnings('ignore', message='numpy.dtype size changed')
warnings.filterwarnings('ignore', message='numpy.ufunc size changed')

config      =   None
logger      =   None

__version__ =   '0.0.2'

# Define global variables
data        =   {}


def set_logging_level(verbose=False):
    import os, sys, logging
    
    logger = logging.getLogger(__name__)
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info('set logging level (verbose:%s) -- %s', verbose, logger.getEffectiveLevel())


def init_load_config(filename='conf/config.yml'):
    import os, sys, logging
    import yaml
    from pkg_resources import resource_string, resource_exists, resource_stream
    
    global config
    logger = logging.getLogger(__name__)
    
    if resource_exists(__name__, filename):
        logger.info('initializing package configuration (file:%s)', filename)
        config = yaml.safe_load(resource_string(__name__, filename))
        logger.debug('initialized package configuration:%s', config)
    else:
        raise ValueError('missing config file:%s' % filename)


def init_load_logging(filename='conf/logging.yml', logpath='logs'):
    import os, sys, logging
    import logging.config
    import yaml
    from pkg_resources import resource_string, resource_exists, resource_stream, resource_filename
    
    logger = logging.getLogger(__name__)
    
    if resource_exists(__name__, filename):
        logger.info('initializing logging configuration (file:%s)', filename)
        logging_config = yaml.safe_load(resource_string(__name__, filename))
        if resource_exists(__name__, logpath):
            for handler, vdict in logging_config.get('handlers', {}).items():
                logfile = vdict.get('filename')
                if logfile:
                    logging_config['handlers'][handler]['filename'] = os.path.join(resource_filename(__name__, logpath), logfile)
        logging.config.dictConfig(logging_config)
        logger.debug('initialized logging configuration:%s', logging_config)
    else:
        raise ValueError('missing config file:%s' % filename)


def init_load_providers(filename=None):
    data['providers']       =   _init_load_datafile('providers', filename)


def init_load_handsets(filename=None):
    data['handsets']        =   _init_load_datafile('handsets', filename)


def _init_load_datafile(label, filename=None, headers=None):
    """
    Helper method to load data files
    """
    import os, sys, logging
    import pandas as pd
    from pkg_resources import resource_string, resource_exists, resource_stream
    
    global config
    logger = logging.getLogger(__name__)
    
    if config is None:
        init_load()
    
    if filename is None:
        filename = 'pkg_data/{0}'.format(config['data'][label])
    
    if resource_exists(__name__, filename):
        if isinstance(headers, list):
            logger.info('initializing %s (file:%s headers:%s)', label, filename, headers)
            return pd.read_csv(resource_stream(__name__, filename), header=0, names=headers)
        else:
            logger.info('initializing %s (file:%s)', label, filename)
            return pd.read_csv(resource_stream(__name__, filename))
    else:
        raise ValueError('missing %s data file:%s' % (label, filename))


def init_load(files=[]):
    """
    Helper method to load all configuration and data
    """
    import os, sys, logging
    
    logger = logging.getLogger(__name__)
    if not files:
        files   =   [   'providers', 'handsets'  ]
    
    init_load_config()
    init_load_logging()
    init_env()
    
    for file in files:
        func = getattr(sys.modules[__name__], '_'.join(['init_load', file]), None)
        if callable(func):
            func()
        else:
            logger.warning('cannot call init loader for file:%s', file)


def init_env(**kwargs):
    import os, sys, logging
    
    global config
    logger = logging.getLogger(__name__)
    
    if not kwargs:
        pass
    
    for var, value in config.get('env', {}).items():
        if value is not None:
            logger.info('setting OS environment variable:%s to value:%s', var, value)
            os.environ[var] = value



class DryRunError(Exception):
    
    def __init__(self, value=None):
        self.value = value if value else 'dry-run caught'
    
    
    def __str__(self):
        return repr(self.value)



class ClobberError(Exception):
    
    def __init__(self, value=None):
        self.value = value if value else 'clobber caught'
    
    
    def __str__(self):
        return repr(self.value)



class TaskError(Exception):
    
    def __init__(self, value=None):
        self.value = value if value else 'task error caught'
    
    
    def __str__(self):
        return repr(self.value)


#