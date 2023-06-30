FROM ebloc/eblocbroker
WORKDIR /workspace/ebloc-broker
RUN git fetch --all --quiet >/dev/null 2>&1 \
 && git pull --all -r -v >/dev/null 2>&1 \
 && cp /workspace/ebloc-broker/docker/config/network-config.yaml ~/.brownie/ \
 && pip install --upgrade pip \
 # && pip install -e . --use-deprecated=legacy-resolver \
 && /workspace/ebloc-broker/broker/bash_scripts/_folder_setup.sh \
 && /workspace/ebloc-broker/broker/python_scripts/add_bloxberg_into_network_config.py \
 && eblocbroker init --base \
 && eblocbroker >/dev/null 2>&1 \
 && /workspace/ebloc-broker/broker/eblocbroker_scripts/get_owner.py

RUN ipfs init \
 && rm -rf ~/.ipfs \
 && ipfs init

RUN cp /workspace/ebloc-broker/docker/bashrc ~/.bashrc
RUN cp /workspace/ebloc-broker/docker/config/cfg.yaml ~/.ebloc-broker/cfg.yaml
RUN cp /workspace/ebloc-broker/docker/config/accounts.tar.gz ~/.brownie/accounts/accounts.tar.gz \
 && tar -xvf ~/.brownie/accounts/accounts.tar.gz -C ~/.brownie/accounts/
RUN /workspace/ebloc-broker/docker/scripts/select_user.py

# overwrites previous docker-entrypoint.sh file
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY supervisord.conf /etc/

RUN echo "password" > /root/.ebloc-broker/.gpg_pass.txt
WORKDIR /workspace/ebloc-broker
