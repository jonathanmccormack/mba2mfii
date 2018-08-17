# -*- coding: utf-8 -*-

import os
import sys
import re

from setuptools import setup, find_packages


def get_version():
    """
    Returns version string by using regex to parse package init file for __version__ variable
    """
    import re
    
    vfile   =   os.path.join('mba2mfii', '__init__.py')
    regex   =   r'^(?:__version__)(?:\s*)=(?:\s*)(?:[\'"]([^\'"]*)[\'"]).*$'
    
    with open(vfile, 'rt') as fp:
        for line in fp.readlines():
            mo = re.search(regex, line, re.M)
            if mo:
                return mo.group(1)
    raise RuntimeError('Unable to find version string in %s.' % (vfile,))


requirements = [
    'Click',
    'click-plugins',
    'pandas',
    'PyYAML',
    'six'   ]

setup(
    name='mba2mfii',
    version=get_version(),
    requires_python='>=2.7',
    description='MBA2MFII is a tool to convert MBA-exported JSON file inputs into an MF-II Challenge Speed Test CSV file output',
    license='BSD',
    author='Jonathan McCormack',
    url='http://github.com/jonathanmccormack/mba2mfii',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Communications',
        'Topic :: Utilities' ])


#
