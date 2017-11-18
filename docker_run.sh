#!/bin/bash
# Usage:
#   docker build -t pynag .
#   docker run -v $(pwd):/mnt pynag

set -ex

PYTHON_VERSION=$1

PYTHON_VERSIONS="
2.6.9
2.7.14
3.6.3"

if [[ "${PYTHON_VERSION}x" == "x" ]]; then
    echo "Usage: $0 <python_version>"
    echo "<python_version> is one of $(echo ${PYTHON_VERSIONS} | xargs echo)"
    echo "ex: $0 3.6.3"
    exit 1
fi
echo "TARGET VERSION=${PYTHON_VERSION:?}"

PYENV_BASE="/home/travis/.pyenv/versions/${PYTHON_VERSION:?}"

rsync -a --exclude=".git" --exclude="*.pyc" --exclude=".python-version" --exclude="__pycache__" /mnt/ /opt/pynag/

sudo service nagios3 start

cd /opt/pynag/

export PATH=${PYENV_BASE:?}/bin:/usr/sbin:$PATH
source ~/.bash_profile
pyenv global ${PYTHON_VERSION:?}

pip install unittest2==1.1.0
pip install coveralls
pip install mock
python setup.py build
python setup.py install

cat <<EOT


======================================
pynag unittest
======================================

EOT

coverage run --source=pynag tests/test.py
