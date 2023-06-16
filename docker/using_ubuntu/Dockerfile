# syntax=docker/dockerfile:1
FROM golang:latest
RUN apt-get install -y ca-certificates
ARG IPFS_TAG=v0.20.0
RUN wget --no-check-certificate -q "https://dist.ipfs.io/go-ipfs/"${IPFS_TAG}"/go-ipfs_"${IPFS_TAG}"_linux-amd64.tar.gz" \
 && tar -xf "go-ipfs_"${IPFS_TAG}"_linux-amd64.tar.gz" \
 && rm -f go-ipfs_${IPFS_TAG}_linux-amd64.tar.gz \
 && cd go-ipfs \
 && make install \
 && ./install.sh

RUN git clone https://github.com/prasmussen/gdrive.git /workspace/gdrive \
 && cd /workspace/gdrive \
 && go env -w GO111MODULE=auto \
 && go get github.com/prasmussen/gdrive

FROM ethereum/client-go:latest
FROM library/mongo:latest
FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.pyenv/shims:/root/.pyenv/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/bin:$PATH"
ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
EXPOSE 6817 6818 6819 6820 3306

COPY --from=0 /go /go
COPY --from=0 /usr/local/bin /usr/local/bin
COPY --from=0 /usr/local/go /usr/local/go
COPY --from=0 /workspace/gdrive /workspace/gdrive
COPY --from=1 /usr/local/bin /usr/local/bin
COPY --from=2 /usr/bin/mongo* /usr/local/bin
RUN useradd -ms /bin/bash mongodb \
  && mkdir -p /var/log/mongodb \
  && mkdir -p /var/lib/mongodb \
  && mkdir -p /data/db \
  && chown -R mongodb /var/log/mongodb \
  && chown -R mongodb /var/lib/mongodb \
  && chown mongodb:mongodb /data/db

ENV GOPATH=/go
ENV GOROOT=/usr/local/go
ENV PATH /go/bin:/usr/local/go/bin:$PATH

## Add Tini
## ========
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

RUN apt update \
 && apt install software-properties-common -y \
 && add-apt-repository ppa:deadsnakes/ppa -y \
 && apt update \
 && apt-get update \
 && apt-get install -y --no-install-recommends --assume-yes \
    python2 \
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
    members \
    pv \
    rsync \
    pigz \
    zlib1g-dev \
    make \
    npm \
    nodejs \
    sudo \
    gcc \
    munge \
    libmunge-dev \
    libboost-all-dev \
    libmunge2 \
    default-mysql-client \
    default-mysql-server \
    software-properties-common \
    mailutils \
    unzip \
    supervisor \
    nano \
    less \
    git \
    libmariadbd-dev \
    libcurl4 \
    mysql-server

# RUN apt-get update \
#  && apt-get install -y --no-install-recommends --assume-yes apt-utils \
#  && apt-get install -y --no-install-recommends --assume-yes \
#     git

# mariadb-server \
# default-libmysqlclient-dev \
# libmariadbd-dev

RUN python3.8 -m venv /opt/venv
#: enable venv
ENV PATH="/opt/venv/bin:$PATH"
## ebloc-broker
# -=-=-=-=-=-=- #: 'pip install -e .' takes few minutes
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

RUN npm config set fund false \
 && npm config set update-notifier false \
 && npm install n -g \
 && npm install -g ganache

## install slurm
RUN git config --global advice.detachedHead false
WORKDIR /workspace
ENV SLURM_VERSION slurm-23-02-2-1
RUN git clone -b ${SLURM_VERSION} --single-branch --depth 1 https://github.com/SchedMD/slurm.git \
 && cd slurm \
 && ./configure --prefix=/usr --sysconfdir=/etc/slurm --with-mysql_config=/usr/bin --libdir=/usr/lib64 \
 && make \
 && make -j 4 install \
 && install -D -m644 etc/cgroup.conf.example /etc/slurm/cgroup.conf.example \
 && install -D -m644 etc/slurm.conf.example /etc/slurm/slurm.conf.example \
 && install -D -m600 etc/slurmdbd.conf.example /etc/slurm/slurmdbd.conf.example \
 && install -D -m644 contribs/slurm_completion_help/slurm_completion.sh /etc/profile.d/slurm_completion.sh \
 && cd .. \
 && rm -rf slurm \
 && slurmctld -V \
 && groupadd -r slurm  \
 && useradd -r -g slurm slurm \
 && mkdir -p /etc/sysconfig/slurm \
     /var/spool/slurmd \
     /var/spool/slurmctld \
     /var/log/slurm \
     /var/run/slurm \
 && chown -R slurm:slurm /var/spool/slurmd \
    /var/spool/slurmctld \
    /var/log/slurm \
    /var/run/slurm

WORKDIR /workspace/ebloc-broker/empty_folder
RUN brownie init \
  && cd ~ \
  && rm -rf /workspace/ebloc-broker/empty_folder \
  && /workspace/ebloc-broker/broker/python_scripts/add_bloxberg_into_network_config.py \
  && cd /workspace//ebloc-broker/contract \
  && brownie compile

# orginize slurm files
RUN chown root:munge -R /etc/munge /etc/munge/munge.key /var/lib/munge  # works but root is alright?
WORKDIR /var/log/slurm
WORKDIR /var/run/supervisor
COPY docker/provider/supervisord.conf /etc/

# mark externally mounted volumes
VOLUME ["/var/lib/mysql", "/var/lib/slurmd", "/var/spool/slurm", "/var/log/slurm", "/run/munge"]
COPY --chown=slurm docker/provider/slurm.conf /etc/slurm/slurm.conf
COPY --chown=slurm docker/provider/slurmdbd.conf /etc/slurm/slurmdbd.conf
RUN chmod 0600 /etc/slurm/slurmdbd.conf

## final operations
RUN ipfs version \
 && ipfs init --profile=lowpower \
 && ipfs config Reprovider.Strategy roots \
 && ipfs config Routing.Type none \
 && /workspace/ebloc-broker/broker/bash_scripts/ubuntu_clean.sh >/dev/null 2>&1 \
 # && echo "alias ls='ls -h --color=always -v --author --time-style=long-iso'" >> ~/.bashrc \
 # && echo "export SQUEUE_FORMAT=\"%8i %9u %5P %2t %12M %12l %5D %3C %30j\"v" >> ~/.bashrc \
 && cp /workspace/ebloc-broker/docker/bashrc ~/.bashrc

COPY docker/config/*.json /root/.brownie/accounts/

WORKDIR /workspace/ebloc-broker/broker
CMD ["/bin/bash"]

COPY docker/provider/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
