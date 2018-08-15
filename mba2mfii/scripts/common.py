# -*- coding: utf-8 -*-

import os, sys

import mba2mfii
from mba2mfii.tasks import Task

import click

from glob import glob


# Main options


def device_id_option(f):
    def callback(ctx, param, value):
        task = ctx.ensure_object(Task)
        if value:
            task.args['device_id'] = value
        return value
    return click.option('-d', '--device-id',
                        required=False,
                        type=int,
                        help='Override device detection and use specified Device ID',
                        callback=callback)(f)


def device_imei_option(f):
    def callback(ctx, param, value):
        task = ctx.ensure_object(Task)
        if value:
            if value.isdigit() and (len(value) in range(15, 17)):
                task.args['device_imei'] = value
            else:
                raise click.BadParameter('Device IMEI must be a string of between 15 and 16 digits')
        return value
    return click.option('-i', '--device-imei',
                        required=False,
                        type=str,
                        help='Use specified Device IMEI',
                        callback=callback)(f)


def provider_id_option(f):
    def callback(ctx, param, value):
        task = ctx.ensure_object(Task)
        if value:
            task.args['provider_id'] = value
        return value
    return click.option('-p', '--provider-id',
                        required=False,
                        type=int,
                        help='Override provider detection and use specified Provider ID',
                        callback=callback)(f)

# Input options



# Output options



# Common options

def clobber_option(f):
    def callback(ctx, param, value):
        task = ctx.ensure_object(Task)
        task.args['clobber'] = value
        return value
    return click.option('--clobber/--no-clobber', default=False,
                        help='Overwrite existing output files',
                        callback=callback)(f)


def dry_run_option(f):
    def callback(ctx, param, value):
        task = ctx.ensure_object(Task)
        task.args['dry_run'] = value
        return value
    return click.option('--dry-run/--no-dry-run', default=False,
                        help='Conduct dry-run of action',
                        callback=callback)(f)


def verbose_option(f):
    def callback(ctx, param, value):
        mba2mfii.set_logging_level(value)
        return value
    return click.option('--verbose/--no-verbose', default=False,
                        help='Toggle for logging verbosity between INFO and DEBUG',
                        callback=callback)(f)


# Input / output arguments

def input_argument(f):
    def callback(ctx, param, value):
        task = ctx.ensure_object(Task)
        
        for input in value:
            if os.path.isdir(input):
                task.input.extend(glob(os.path.join(input, '*.json')))
            else:
                task.input.append(input)
        
        return task.input
    return click.argument('input',
                        nargs=-1,
                        type=click.Path(exists=True),
                        callback=callback)(f)


def output_argument(f):
    def callback(ctx, param, value):
        task = ctx.ensure_object(Task)
        
        task.output = value
        
        return value
    return click.argument('output',
                        required=True,
#                       type=click.File(mode='w'),
                        callback=callback)(f)


# Common decorators

def common_options(f):
    for func in [ clobber_option, dry_run_option, verbose_option ]:
        f = func(f)
    return f


def data_options(f):
    for func in [ device_id_option, device_imei_option, provider_id_option ]:
        f = func(f)
    return f


def input_options(f):
    for func in [ ]:
        f = func(f)
    return f


def input_args_and_options(f):
    for func in [ input_argument, input_options ]:
        f = func(f)
    return f


def output_options(f):
    for func in [ ]:
        f = func(f)
    return f


def output_args_and_options(f):
    for func in [ output_argument, output_options ]:
        f = func(f)
    return f



#