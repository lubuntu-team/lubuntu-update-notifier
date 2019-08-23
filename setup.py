#!/usr/bin/env python3
# coding=utf-8

# Copyright (C) 2019 Hans P. Möller <hmollercl@lubuntu.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

setup(
    name="lubuntu-update-notifier",
    version="0.1",
    packages=['lubuntu-update-notifier'],
    scripts=['lubuntu-upgrader'],
    data_files=[
                  ('lib/lubuntu-update-notifier/',
                   ['lubuntu-upg-notifier.sh', 'lubuntu-notifier.py'])]
)
