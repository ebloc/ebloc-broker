# syntax=docker/dockerfile:1
FROM golang:latest
RUN apt-get install -y ca-certificates
RUN wget --no-check-certificate -q "https://dist.ipfs.io/go-ipfs/v0.11.0/go-ipfs_v0.11.0_linux-amd64.tar.gz" \
 && tar -xvf "go-ipfs_v0.11.0_linux-amd64.tar.gz" \
 && rm -f go-ipfs_v0.11.0_linux-amd64.tar.gz
WORKDIR go-ipfs
RUN make install \
 && ./install.sh

RUN git clone https://github.com/prasmussen/gdrive.git /workspace
WORKDIR /workspace/gdrive
RUN go env -w GO111MODULE=auto \
 && go get github.com/prasmussen/gdrive

FROM python:3.7
# ENV VIRTUAL_ENV=/opt/venv
# RUN python3 -m venv $VIRTUAL_ENV
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.pyenv/shims:/root/.pyenv/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/bin:$PATH"
ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
EXPOSE 6817 6818 6819 6820 3306

## ebloc-broker -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
RUN apt-get update \
 && apt-get install -y --no-install-recommends --assume-yes apt-utils \
 && apt-get install -y --no-install-recommends --assume-yes \
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
    # slurm-packages
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
 && eblocbroker >/dev/null 2>&1 \
 && ./broker/_utils/yaml.py >/dev/null 2>&1

COPY --from=0 /go /go
COPY --from=0 /usr/local/bin /usr/local/bin
COPY --from=0 /usr/local/go /usr/local/go
COPY --from=0 /workspace/gdrive /workspace/gdrive

ENV GOPATH=/go
ENV GOROOT=/usr/local/go
ENV PATH /go/bin:/usr/local/go/bin:$PATH

# Instal SLURM
# -=-=-=-=-=-=
# Add Tini
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

RUN git config --global advice.detachedHead false
WORKDIR /workspace
ARG JOBS=4
RUN git clone -b slurm-19-05-8-1 --single-branch --depth 1 https://github.com/SchedMD/slurm.git \
 && cd slurm \
 && ./configure --prefix=/usr --sysconfdir=/etc/slurm --enable-slurmrestd \
   --with-mysql_config=/usr/bin --libdir=/usr/lib64 \
 && make \
 && make -j ${JOBS} install \
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

RUN chown root:munge -R /etc/munge /etc/munge/munge.key /var/lib/munge  # works but root is alright?
WORKDIR /var/log/slurm
WORKDIR /var/run/supervisor
COPY broker/_slurm/files/supervisord.conf /etc/

# Mark externally mounted volumes
VOLUME ["/var/lib/mysql", "/var/lib/slurmd", "/var/spool/slurm", "/var/log/slurm", "/run/munge"]

COPY --chown=slurm broker/_slurm/files/slurm/slurm.conf /etc/slurm/slurm.conf
COPY --chown=slurm broker/_slurm/files/slurm/gres.conf /etc/slurm/gres.conf
COPY --chown=slurm broker/_slurm/files/slurm/slurmdbd.conf /etc/slurm/slurmdbd.conf
RUN chmod 0600 /etc/slurm/slurmdbd.conf

## mongodb
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add - \
 && echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-4.4.list \
 && apt-get update \
 && apt-get install -y mongodb-org \
 && mkdir -p /data/db \
 && chown -R mongodb. /var/log/mongodb \
 && chown -R mongodb. /var/lib/mongodb \
 && chown mongodb:mongodb /data/db

## Finally
WORKDIR /workspace/ebloc-broker/broker
RUN apt-get clean \
 && apt-get autoremove \
 && apt-get autoclean \
 && ipfs version \
 && ganache --version

COPY broker/_slurm/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["/bin/bash"]

# -=-=-=-=-=-=-=-=-=-=-=-=- DELETE -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# RUN git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/powerlevel10k \
#  && echo "source ~/powerlevel10k/powerlevel10k.zsh-theme" >> ~/.zshrc \
#  && ipfs version \
#  && ganache --version

# COPY --from=1 /opt/venv /opt/venv  # /opt/venv/bin
# COPY --from=1 /usr/local/lib/node_modules /usr/local/lib/node_modules
# COPY --from=1 /usr/local/bin /usr/local/bin
# COPY --from=1 /workspace/ebloc-broker /workspace/ebloc-broker

# COPY --from=1 /usr/local/sbin/ /usr/local/sbin/
# COPY --from=1 /usr/local/bin /usr/local/bin
# COPY --from=1 /usr/local/lib /usr/local/lib
