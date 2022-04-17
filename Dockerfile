# syntax=docker/dockerfile:1
FROM golang:latest
RUN  apt-get install -y ca-certificates
RUN wget --no-check-certificate -q "https://dist.ipfs.io/go-ipfs/v0.11.0/go-ipfs_v0.11.0_linux-amd64.tar.gz"
RUN tar -xvf "go-ipfs_v0.11.0_linux-amd64.tar.gz"
WORKDIR go-ipfs
RUN make install
RUN ./install.sh

WORKDIR /workspace
RUN git clone https://github.com/prasmussen/gdrive.git
WORKDIR /workspace/gdrive
RUN go env -w GO111MODULE=auto
RUN go get github.com/prasmussen/gdrive
# RUN go build -ldflags "-w -s"

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
FROM python:3.7
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
 && apt-get install -y libdbus-1-dev \
    libdbus-glib-1-dev \
    libgirepository1.0-dev \
    libssl-dev \
    npm

ENV NODE_OPTION=--openssl-legacy-provider
RUN npm config set fund false
RUN npm config set update-notifier false
RUN npm install -g npm@latest
RUN npm install -g ganache
RUN ganache --version

WORKDIR /workspace
RUN git clone https://github.com/ebloc/ebloc-broker.git
WORKDIR /workspace/ebloc-broker
RUN git checkout dev
RUN git fetch --all --quiet >/dev/null 2>&1
RUN git pull --all -r -v >/dev/null 2>&1
RUN pip install -U pip wheel
#: takes few minutes
RUN pip install -e . #  --use-deprecated=legacy-resolver
# RUN if python -c "import broker" &> /dev/null; then pip install -e . --use-deprecated=legacy-resolver; fi
RUN eblocbroker >/dev/null 2>&1  # final check

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
FROM python:3.7
RUN apt-get update \
 && apt-get install -y build-essential \
    gcc \
    g++ \
    apt-utils \
    software-properties-common \
    git \
    tree \
    wget \
    curl \
    members \
    zsh \
    nano \
    pv \
    rsync \
    pigz \
    python-setuptools \
    libssl-dev \
    zlib1g-dev \
    make \
    vim

COPY --from=0 /go /go
COPY --from=0 /usr/local/bin /usr/local/bin
COPY --from=0 /usr/local/go /usr/local/go
COPY --from=0 /workspace/gdrive /workspace/gdrive
COPY --from=1 /opt/venv /opt/venv
COPY --from=1 /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=1 /usr/local/bin /usr/local/bin
COPY --from=1 /workspace/ebloc-broker /workspace/ebloc-broker

ENV GOPATH=/go
ENV GOROOT=/usr/local/go
ENV PATH /opt/venv/bin:/go/bin:/usr/local/go/bin:$PATH
RUN [ ! -d ~/powerlevel10k ] && git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/powerlevel10k
RUN echo "source ~/powerlevel10k/powerlevel10k.zsh-theme" >> ~/.zshrc

RUN ipfs version
RUN ganache --version
