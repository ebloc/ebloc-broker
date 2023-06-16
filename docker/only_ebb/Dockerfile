# syntax=docker/dockerfile:1
FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.pyenv/shims:/root/.pyenv/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/bin:$PATH"
ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
RUN apt update \
 && apt install software-properties-common -y \
 && add-apt-repository ppa:deadsnakes/ppa -y \
 && apt update \
 && apt-get update \
 && apt-get install -y --no-install-recommends --assume-yes \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-virtualenv \
    python3.8 \
    python3.8-dev \
    python3.8-venv

RUN apt-get update \
 && apt-get install -y --no-install-recommends --assume-yes apt-utils \
 && apt-get install -y --no-install-recommends --assume-yes \
    acl \
    aptitude \
    build-essential \
    dbus \
    libdbus-1-dev \
    libdbus-glib-1-dev \
    libgirepository1.0-dev \
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    make \
    sudo \
    gcc \
    libboost-all-dev \
    software-properties-common \
    unzip \
    supervisor \
    git \
    libcurl4

RUN python3.8 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /workspace
RUN git clone https://github.com/ebloc/ebloc-broker.git
WORKDIR /workspace/ebloc-broker
RUN git checkout dev >/dev/null 2>&1 \
 && git fetch --all --quiet >/dev/null 2>&1 \
 && git pull --all -r -v >/dev/null 2>&1 \
 && /opt/venv/bin/python3 -m pip install --upgrade pip \
 && /opt/venv/bin/python3 -m pip install -U pip wheel setuptools dbus-python \
 && /opt/venv/bin/python3 -m pip install --disable-pip-version-check -e . --use-deprecated=legacy-resolver \
 && eblocbroker init --base \
 && eblocbroker >/dev/null 2>&1 \
 && ./broker/_utils/yaml.py >/dev/null 2>&1
