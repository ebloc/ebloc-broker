# syntax=docker/dockerfile:1
FROM python:3.7
ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"

ENV PATH "/root/.pyenv/shims:/root/.pyenv/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/bin"
EXPOSE 6817 6818 6819 6820 3306

RUN apt-get update \
 && apt-get install -y --no-install-recommends apt-utils \
 && apt-get install -y git \
     build-essential \
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
 && apt clean

# Add Tini
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

RUN git config --global advice.detachedHead false
WORKDIR /workspace
ARG JOBS=4
RUN git clone -b slurm-19-05-8-1 --single-branch --depth 1 https://github.com/SchedMD/slurm.git \
 && cd slurm \
 && ./configure --enable-debug --enable-front-end -prefix=/usr --sysconfdir=/etc/slurm \
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
    /var/run/slurm \
 && chown -R munge:munge /var/log/munge

WORKDIR /usr/local/var/log/munge
WORKDIR /run/munge
# RUN /sbin/create-munge-key

WORKDIR /var/log/slurm
WORKDIR /var/run/supervisor
COPY files/supervisord.conf /etc/

# Mark externally mounted volumes
VOLUME ["/var/lib/mysql", "/var/lib/slurmd", "/var/spool/slurm", "/var/log/slurm", "/run/munge"]

COPY --chown=slurm files/slurm/slurm.conf /etc/slurm/slurm.conf
COPY --chown=slurm files/slurm/gres.conf /etc/slurm/gres.conf
COPY --chown=slurm files/slurm/slurmdbd.conf /etc/slurm/slurmdbd.conf
RUN chmod 0600 /etc/slurm/slurmdbd.conf

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["/bin/bash"]

# RUN chown root:root /var/log/munge


# https://github.com/giovtorres/docker-centos7-slurm/blob/main/Dockerfile

# docker build -t slurm:latest . --progress plain
# docker run -it slurm bash
