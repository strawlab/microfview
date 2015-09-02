#!/usr/bin/env python2
# coding=utf-8

# Authors: John Stowers <john.stowers@gmail.com>
# Licence: BSD 3 clause

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import microfview

setup(
    name='microfview',
    license='BSD 3 clause',
    description='Simple image processing scaffold',
    long_description=open('README.rst').read(),
    version=microfview.__version__,
    author='John Stowers',
    author_email='john.stowers@gmail.com',
    packages=['microfview',],
    scripts=['bin/micro-fview'],
    include_package_data=True,
)

