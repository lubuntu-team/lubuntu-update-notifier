#!/usr/bin/env python3

from setuptools import setup
#from distutils.core import setup
#from DistUtilsExtra.command import *

setup(
    name="lubuntu-update-notifier",
    version="0.1",
    packages=['lubuntu-update-notifier'],
    scripts=['upgrader.py'],
    data_files=[
                  ('lib/lubuntu-update-notifier/',
                   ['upg-notifier.sh','notifier.py'])]
)
