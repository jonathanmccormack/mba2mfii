# -*- coding: utf-8 -*-

import os, sys

import importlib
import logging
logger = logging.getLogger(__name__)

import click

import mba2mfii
#from mba2mfii.tools import symbolize, get_folders_by_regex, get_mdict_folders, get_layers
from mba2mfii.tasks import Task
from mba2mfii.api import MBAExport

from mba2mfii.scripts.common  import *


# Click commands

CONTEXT_SETTINGS = dict(help_option_names=[ '-h', '--help' ], token_normalize_func=lambda x: x.lower())

pass_task = click.make_pass_decorator(Task, ensure=True)

@click.command(context_settings=CONTEXT_SETTINGS)
@input_argument
@output_argument
@data_options
@common_options
@click.version_option(version='0.0.1')
@pass_task
def cli(task, input, output, **kwargs):
    """
    MBA2MFII is designed to quickly and accurately convert data from the 
    Measuring Mobile Broadband America (aka "MBA" or "FCC Speed Test") app
    released by the Federal Communications Commission into the Challenge Speed
    Test CSV file format required for the Mobility Fund Phase II Challenge
    Process.
    
    Data recorded by the FCC Speed Test app can be exported in JSON format,
    which must be converted in order to be uploaded into the MF-II Challenge
    Process Portal, hosted by the Universal Service Administrative Company.
    """
    mba2mfii.init_load()
    mba2mfii.set_logging_level(kwargs.get('verbose', False))
    
    logger.debug('calling core command mba2mfii cli')
    
    for fp in task.input:
        logger.info('processing file:%s', fp)
        try:
            input = MBAExport(fp, **task.args)
            df = input.to_dataframe()
            if df.empty:
                logger.warn('empty dataframe from MBA export:%s', fp)
            else:
                task.build_output(df) 
        except TypeError:
            logger.error('cannot load MBA export:%s', fp)
            raise
    
    task.write_output(output)



#