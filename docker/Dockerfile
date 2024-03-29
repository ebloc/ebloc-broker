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

FROM python:3.7
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

ENV GOPATH=/go
ENV GOROOT=/usr/local/go
ENV PATH /go/bin:/usr/local/go/bin:$PATH

## Add Tini
## ========
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

# Install mongodb
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-5.0.asc | tee /etc/apt/trusted.gpg.d/mongodb.asc > /dev/null \
 && echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-5.0.list \
 && apt-get update \
 && apt-get install -y mongodb-org \
 && mkdir -p /data/db \
 && chown -R mongodb. /var/log/mongodb \
 && chown -R mongodb. /var/lib/mongodb \
 && chown mongodb:mongodb /data/db

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
    members \
    pv \
    rsync \
    pigz \
    zlib1g-dev \
    make \
    default-mysql-server \
    npm \
    nodejs \
    python3-venv \
    sudo \
    netcat \
    ## required packages to install for Slurm
    gcc \
    munge \
    libmunge-dev \
    libboost-all-dev \
    libmunge2 \
    default-mysql-client \
    default-mysql-server \
    software-properties-common \
    default-libmysqlclient-dev \
    mailutils \
    unzip \
    libmariadbd-dev \
    mariadb-server \
    supervisor \
    nano \
    less \
 && apt-get clean

RUN npm config set fund false \
 && npm config set update-notifier false \
 && npm install n -g \
 && n latest \
 && hash -r \
 && npm install -g npm@latest \
 && npm install -g ganache

RUN python3 -m venv /opt/venv
#: enable venv
ENV PATH="/opt/venv/bin:$PATH"

## install slurm
RUN git config --global advice.detachedHead false
WORKDIR /workspace
ENV SLURM_VERSION slurm-19-05-8-1
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

## ebloc-broker
# -=-=-=-=-=-=-
WORKDIR /workspace
RUN git clone https://github.com/ebloc/ebloc-broker.git
WORKDIR /workspace/ebloc-broker
#: `pip install -e .` takes few minutes
RUN git checkout dev >/dev/null 2>&1 \
 && git fetch --all --quiet >/dev/null 2>&1 \
 && git pull --all -r -v >/dev/null 2>&1 \
 && pip install --upgrade pip \
 && pip install -U pip wheel setuptools  dbus-python \
 && pip install -e . --use-deprecated=legacy-resolver \
 && mkdir -p ~/.cache/black/$(pip freeze | grep black | sed 's|black==||g') \
 && eblocbroker init --base \
 && eblocbroker >/dev/null 2>&1 \
 && ./broker/_utils/yaml.py >/dev/null 2>&1

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
RUN echo "0f8f4d5" \
 && ipfs version \
 && ipfs init --profile=lowpower \
 && ipfs config Reprovider.Strategy roots \
 && ipfs config Routing.Type none \
 && /workspace/ebloc-broker/broker/bash_scripts/ubuntu_clean.sh >/dev/null 2>&1 \
 # && echo "alias ls='ls -h --color=always -v --author --time-style=long-iso'" >> ~/.bashrc \
 # && echo "export SQUEUE_FORMAT=\"%8i %9u %5P %2t %12M %12l %5D %3C %30j\"v" >> ~/.bashrc \
 && cp /workspace/ebloc-broker/docker/bashrc ~/.bashrc

WORKDIR /workspace/ebloc-broker/broker
CMD ["/bin/bash"]

COPY docker/provider/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
