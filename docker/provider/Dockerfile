FROM eblocbroker/app:latest
WORKDIR /workspace/ebloc-broker
RUN git fetch --all --quiet >/dev/null 2>&1 \
 && git pull --all -r -v >/dev/null 2>&1 \
 && pip install --upgrade pip \
 # && pip install -e . --use-deprecated=legacy-resolver \
 && cp /workspace/ebloc-broker/docker/config/network-config.yaml ~/.brownie/ \
 && /workspace/ebloc-broker/broker/bash_scripts/_folder_setup.sh \
 &&
/workspace/ebloc-broker/broker/python_scripts/add_bloxberg_into_network_config.py \
 && eblocbroker init --base \
 && eblocbroker >/dev/null 2>&1 \
 && /workspace/ebloc-broker/broker/eblocbroker_scripts/get_owner.py

RUN cp /workspace/ebloc-broker/docker/bashrc ~/.bashrc
RUN cp /workspace/ebloc-broker/docker/config/cfg.yaml ~/.ebloc-broker/cfg.yaml
RUN cp /workspace/ebloc-broker/docker/config/accounts.tar.gz
~/.brownie/accounts/accounts.tar.gz \
 && tar -xvf ~/.brownie/accounts/accounts.tar.gz -C ~/.brownie/accounts/
RUN /workspace/ebloc-broker/docker/scripts/select_user.py

WORKDIR /workspace/ebloc-broker
RUN git fetch --all --quiet >/dev/null 2>&1 \
 && git pull --all -r -v >/dev/null 2>&1
