#!/bin/bash -ex

apt-get update && \
apt-get -y install python3 \
                   python3-dev \
                   python3-pip \
                   python3-virtualenv \
                   \
                   libffi-dev \
                   libpq-dev \
                   \
                   ffmpeg
