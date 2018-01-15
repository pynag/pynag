#!/bin/bash
#
# Usage:
#   docker run --rm -it -v $(pwd):/mnt centos:6 /mnt/rpm-build.sh
#   docker run --rm -it -v $(pwd):/mnt centos:7 /mnt/rpm-build.sh


set -xe


[[ -d "/mnt/rpm-build" ]] || mkdir /mnt/rpm-build
yum -y install epel-release
yum -y install rpm-build make rsync python-devel python-setuptools python-unittest2 python-six
cp -r /mnt /opt/pynag
cd /opt/pynag
make clean
make
rsync -av /opt/pynag/rpm-build/ /mnt/rpm-build/
