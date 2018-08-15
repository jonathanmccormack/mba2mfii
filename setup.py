# -*- coding: utf-8 -*-

import os, sys
from setuptools import setup, find_packages

requirements = [
    'click',
    'click-plugins',
    'pandas',
    'PyYAML' ]

setup(
    name='mba2mfii',
    version='0.0.1',
    requires_python='>=3',
    description='MBA2MFII is a tool to convert MBA-exported JSON file inputs into an MF-II Challenge Speed Test CSV file output',
    license='BSD',
    author='Jonathan McCormack',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points='''
        [console_scripts]
        mba2mfii=mba2mfii.scripts:cli
        ''',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Telecommnications Industry',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Communications',
        'Topic :: Utilities' ])


#
