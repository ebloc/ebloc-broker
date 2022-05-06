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

# Instal SLURM
# ============
FROM python:3.7
WORKDIR /workspace
RUN git config --global advice.detachedHead false \
 && git clone --depth 1 --branch slurm-19-05-8-1 https://github.com/SchedMD/slurm.git
WORKDIR slurm
RUN ./configure --enable-debug --enable-front-end \
 && make \
 && make install \
 && slurmctld -V

FROM python:3.7
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
RUN apt-get update \
 && apt-get install -y --no-install-recommends apt-utils \
 && apt-get install -y --no-install-recommends libdbus-1-dev \
    libdbus-glib-1-dev \
    libgirepository1.0-dev \
    libssl-dev \
    members \
    pv \
    rsync \
    pigz \
    zlib1g-dev \
    make \
    munge \
    libmunge-dev \
    libboost-all-dev \
    libmunge2 \
    default-mysql-client \
    default-mysql-server \
    default-libmysqlclient-dev \
    mailutils \
    npm \
    nodejs \
    libmariadbd-dev \
    mariadb-server
    # build-essential \
    # software-properties-common \
    # tree \
    # python-setuptools \
    # default-libmariadbclient-dev \
    # libmariadb-dev \

RUN npm config set fund false \
 && npm config set update-notifier false \
 && npm install n -g \
 && n latest \
 && hash -r \
 && npm install -g npm@latest \
 && npm install -g ganache

WORKDIR /workspace
RUN git clone https://github.com/ebloc/ebloc-broker.git
WORKDIR /workspace/ebloc-broker
#: pip install takes few minutes
RUN git checkout dev \
 && git fetch --all --quiet >/dev/null 2>&1 \
 && git pull --all -r -v >/dev/null 2>&1 \
 && pip install -U pip wheel \
 && pip install -e . --use-deprecated=legacy-resolver \
 && eblocbroker >/dev/null 2>&1

COPY --from=0 /go /go
COPY --from=0 /usr/local/bin /usr/local/bin
COPY --from=0 /usr/local/go /usr/local/go
COPY --from=0 /workspace/gdrive /workspace/gdrive

COPY --from=1 /usr/local/sbin/ /usr/local/sbin/
COPY --from=1 /usr/local/bin /usr/local/bin
COPY --from=1 /usr/local/lib /usr/local/lib

# COPY --from=1 /opt/venv /opt/venv
# COPY --from=1 /usr/local/lib/node_modules /usr/local/lib/node_modules
# COPY --from=1 /usr/local/bin /usr/local/bin
# COPY --from=1 /workspace/ebloc-broker /workspace/ebloc-broker

ENV GOPATH=/go
ENV GOROOT=/usr/local/go
ENV PATH /opt/venv/bin:/go/bin:/usr/local/go/bin:$PATH

WORKDIR /var/log/slurm
WORKDIR /workspace/ebloc-broker

RUN apt-get clean \
 && apt-get autoremove \
 && apt-get autoclean \
 && ipfs version \
 && ganache --version

 # Configure munge (for SLURM authentication)
RUN mkdir /var/run/munge && \
    chown root /var/lib/munge && \
    chown root /etc/munge && chmod 600 /var/run/munge && \
    chmod 755  /run/munge && \
    chmod 600 /etc/munge/munge.key

VOLUME ["/home", "/.secret"]

#   22:         SSH
# 3306:         MariaDB
# 6817:         Slurm Ctl D
# 6818:         Slurm D
# 6819:         Slurm DBD
EXPOSE 22 3306 6817 6818 6819

# RUN git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/powerlevel10k \
#  && echo "source ~/powerlevel10k/powerlevel10k.zsh-theme" >> ~/.zshrc \
#  && ipfs version \
#  && ganache --version

# https://github.com/GRomR1/docker-slurmbase/blob/master/Dockerfile
# https://github.com/SciDAS/slurm-in-docker/blob/master/base/Dockerfile
# https://stackoverflow.com/questions/42597739/accessing-docker-container-mysql-databases
# https://github.com/giovtorres/docker-centos7-slurm/blob/main/Dockerfile
