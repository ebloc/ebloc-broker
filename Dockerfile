# syntax=docker/dockerfile:1
FROM ebloc/eblocbroker:latest
WORKDIR /workspace/ebloc-broker
RUN echo "doo"
RUN git fetch --all --quiet >/dev/null 2>&1 \
 && git pull --all -r -v >/dev/null 2>&1 \
 && pip install --upgrade pip \
 # && pip install -e . --use-deprecated=legacy-resolver \
 && eblocbroker init --base \
 && eblocbroker >/dev/null 2>&1 \
 && /workspace/ebloc-broker/broker/eblocbroker_scripts/get_owner.py \
 && /workspace/ebloc-broker/broker/python_scripts/add_bloxberg_into_network_config.py \
 && ./broker/_utils/yaml.py >/dev/null 2>&1

RUN cp /workspace/ebloc-broker/docker/bashrc ~/.bashrc
RUN cp /workspace/ebloc-broker/docker/config/cfg.yaml ~/.ebloc-broker/cfg.yaml
RUN cp /workspace/ebloc-broker/docker/config/*.json ~/.brownie/accounts/

WORKDIR ~/.brownie/accounts/
RUN cp /workspace/ebloc-broker/docker/config/accounts.tar.gz ~/.brownie/accounts/accounts.tar.gz \
 && tar -xvf ~/.brownie/accounts/accounts.tar.gz

WORKDIR /workspace/ebloc-broker
