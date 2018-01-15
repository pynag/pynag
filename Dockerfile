# Local Testing Image
#
# Usage:
#   docker build -t pynag .
#
#   docker run --rm -d --name pynag_py27 -v $(pwd):/mnt pynag
#   docker exec -it pynag_py27 sudo -u travis -i /mnt/docker_run.sh 2.7.14
#
#   docker run --rm -d --name pynag_py36 -v $(pwd):/mnt pynag
#   docker exec -it pynag_py36 sudo -u travis -i /mnt/docker_run.sh 3.6.3
FROM ubuntu:trusty
MAINTAINER Toshiaki Baba<toshiaki@netmark.jp>

# basic setup
RUN cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime
RUN localedef -i ja_JP -c -f UTF-8 -A /usr/share/locale/locale.alias ja_JP.UTF-8
ENV LC_ALL ja_JP.UTF-8

# pyenv
RUN apt-get -y update && apt-get -y install \
        curl git build-essential openssl libssl-dev libbz2-dev libreadline-dev libsqlite3-dev \
        rsync \
        nagios3 check-mk-livestatus \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m travis && echo "travis ALL=(ALL) NOPASSWD: ALL " | tee /etc/sudoers.d/travis && chmod 400 /etc/sudoers.d/travis
RUN sudo -u travis -i bash -c 'curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash'
RUN echo 'export PATH="/home/travis/.pyenv/bin:$PATH"'  | tee -a /home/travis/.bash_profile
RUN echo 'eval "$(pyenv init -)"'                       | tee -a /home/travis/.bash_profile
RUN echo 'eval "$(pyenv virtualenv-init -)"'            | tee -a /home/travis/.bash_profile
RUN chown travis /home/travis/.bash_profile
RUN sudo -u travis -i /home/travis/.pyenv/bin/pyenv install 2.6.9
RUN sudo -u travis -i /home/travis/.pyenv/bin/pyenv install 2.7.14
RUN sudo -u travis -i /home/travis/.pyenv/bin/pyenv install 3.6.3

# pynag, nagios
RUN install -d -o travis -g travis /opt/pynag
RUN chmod 777 /etc/nagios3/nagios.cfg
RUN chmod a+rx '/var/cache/nagios3/'
RUN echo "broker_module=/usr/lib/check_mk/livestatus.o /var/lib/nagios3/rw/livestatus" >> /etc/nagios3/nagios.cfg

RUN sudo -u travis -i git config --global user.email "travis@example.com"
RUN sudo -u travis -i git config --global user.name "Travis Local Image"

ENTRYPOINT ["/sbin/init"]
