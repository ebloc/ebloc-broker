# syntax=docker/dockerfile:1
FROM golang:latest
RUN apt-get install -y ca-certificates
RUN wget --no-check-certificate -q "https://dist.ipfs.io/go-ipfs/v0.13.0/go-ipfs_v0.13.0_linux-amd64.tar.gz" \
 && tar -xf "go-ipfs_v0.13.0_linux-amd64.tar.gz" \
 && rm -f go-ipfs_v0.13.0_linux-amd64.tar.gz \
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
EXPOSE 6817 6818 6819 6820 3306 6001 6002

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

## mongodb
## =======
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add - \
 && echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-4.4.list \
 && apt-get update \
 && apt-get install -y mongodb-org \
 && mkdir -p /data/db \
 && chown -R mongodb. /var/log/mongodb \
 && chown -R mongodb. /var/lib/mongodb \
 && chown mongodb:mongodb /data/db

RUN apt-get update \
 && apt-get install -y --no-install-recommends --assume-yes apt-utils \
 && apt-get install -y --no-install-recommends --assume-yes \
    aptitude \
    build-essential \
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
#; enable venv
ENV PATH="/opt/venv/bin:$PATH"

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
 && pip install -U pip wheel setuptools \
 && pip install -e . --use-deprecated=legacy-resolver \
 && mkdir -p ~/.cache/black/$(pip freeze | grep black | sed 's|black==||g') \
 && eblocbroker >/dev/null 2>&1 \
 && ./broker/_utils/yaml.py >/dev/null 2>&1

WORKDIR /workspace/ebloc-broker/empty_folder
RUN brownie init \
  && cd ~ \
  && rm -rf /workspace/ebloc-broker/empty_folder \
  && /workspace/ebloc-broker/broker/python_scripts/add_bloxberg_into_network_config.py \
  && cd /workspace//ebloc-broker/contract \
  && brownie compile

## SLURM
# Compile, build and install Slurm from Git source
# && ./configure --prefix=/usr --sysconfdir=/etc/slurm --with-mysql_config=/usr/bin --libdir=/usr/lib64 --with-hdf5=no \
ARG SLURM_TAG=slurm-22-05-2-1
RUN git config --global advice.detachedHead false
WORKDIR /workspace
RUN git clone -b ${SLURM_TAG} --single-branch --depth 1 https://github.com/SchedMD/slurm.git \
 && cd slurm \
 && ./configure --prefix=/usr --sysconfdir=/etc/slurm --with-mysql_config=/usr/bin --libdir=/usr/lib64 --with-hdf5=no --enable-debug  --enable-multiple-slurmd \
 && make \
 && make -j 4 install \
 && install -D -m644 etc/cgroup.conf.example /etc/slurm/cgroup.conf.example \
 && install -D -m644 etc/slurm.conf.example /etc/slurm/slurm.conf.example \
 && install -D -m600 etc/slurmdbd.conf.example /etc/slurm/slurmdbd.conf.example \
 && install -D -m644 contribs/slurm_completion_help/slurm_completion.sh /etc/profile.d/slurm_completion.sh \
 && cd .. \
 && rm -rf slurm \
 && slurmctld -V \
 && groupadd -r slurm \
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

VOLUME ["/var/lib/mysql", "/var/lib/slurmd", "/var/spool/slurm", "/var/log/slurm", "/run/munge"]
COPY --chown=slurm docker/slurm/files/create-munge-key /sbin/
RUN /sbin/create-munge-key \
 && chown munge:munge -R /run/munge

# # orginize slurm files
# RUN chown root:munge -R /etc/munge/munge.key /etc/munge /var/lib/munge
# # RUN chown root:munge -R /var/lib/munge /etc/munge/munge.key /etc/munge
# RUN chown munge:munge -R /var/lib/munge /etc/munge/munge.key /etc/munge
# RUN chown -R munge: /etc/munge/ /var/log/munge/ /var/lib/munge/ /run/munge/
# RUN chmod 0700 /etc/munge/ /var/log/munge/ /var/lib/munge/ /run/munge/

WORKDIR /var/log/slurm
WORKDIR /var/run/supervisor
COPY docker/slurm/files/supervisord.conf /etc/

# mark externally mounted volumes
COPY --chown=slurm docker/slurm/files/slurm.conf /etc/slurm/slurm.conf
COPY --chown=slurm docker/slurm/files/slurmdbd.conf /etc/slurm/slurmdbd.conf
RUN chmod 0600 /etc/slurm/slurmdbd.conf

## finally
RUN gdrive version \
 && ipfs version \
 && ipfs init \
 && ipfs config Reprovider.Strategy roots \
 && ipfs config Routing.Type none \
 && ganache --version \
 && /workspace/ebloc-broker/broker/bash_scripts/ubuntu_clean.sh >/dev/null 2>&1 \
 && echo "alias ls='ls -h --color=always -v --author --time-style=long-iso'" >> ~/.bashrc \
 && du -sh / 2>&1 | grep -v "cannot"

COPY docker/slurm/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
WORKDIR /workspace/ebloc-broker/broker
CMD ["/bin/bash"]
