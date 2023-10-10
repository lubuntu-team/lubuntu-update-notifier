#!/bin/sh
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

while true;
    do
        OUT=`/usr/lib/update-notifier/apt-check 2>&1`
        oldIFS=$IFS
        IFS=';'
        j=0
        for STRING in $OUT; do
            case $j in
                0)
                    UPG=$STRING;;
                1)
                    SEC=$STRING;;
            esac
             j=`expr $j + 1`
        done
        IFS=$oldIFS

        NEWREL_CHECK=`/usr/bin/do-release-upgrade -c 2>&1`
        NEWREL=$?
        if [ "$NEWREL" -eq 0 ]; then
            VERSION=`echo $NEWREL_CHECK | awk -F\' '/available/{print $2}'`
        fi
        /usr/libexec/lubuntu-update-notifier/lubuntu-notifier.py -u $UPG -s $SEC -r $NEWREL -v $VERSION -p /usr/bin/lubuntu-upgrader
        sleep 86400
done;
