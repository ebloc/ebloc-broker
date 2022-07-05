FROM ebloc/ebloc-broker:latest

## slurm
RUN apt-get install -y --no-install-recommends --assume-yes \
    munge \
    libmunge-dev \
    libboost-all-dev \
    libmunge2 \
    default-mysql-server \
    default-mysql-client \
    default-libmysqlclient-dev \
    mariadb-server \
    mailutils \
    libmariadbd-dev \
 && apt-get clean

# Compile, build and install Slurm from Git source
ARG SLURM_TAG=slurm-22-05-2-1
RUN git config --global advice.detachedHead false
WORKDIR /workspace
RUN git clone -b ${SLURM_TAG} --single-branch --depth 1 https://github.com/SchedMD/slurm.git \
 && cd slurm \
 && ./configure --prefix=/usr --sysconfdir=/etc/slurm --with-mysql_config=/usr/bin --libdir=/usr/lib64 --with-hdf5=no --enable-debug --enable-multiple-slurmd \
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
COPY --chown=slurm create-munge-key /sbin/
RUN /sbin/create-munge-key \
 && chown munge:munge -R /run/munge

WORKDIR /var/log/slurm
WORKDIR /var/run/supervisor
COPY supervisord.conf /etc/

# mark externally mounted volumes
COPY --chown=slurm slurm.conf /etc/slurm/slurm.conf
COPY --chown=slurm slurmdbd.conf /etc/slurm/slurmdbd.conf
RUN chmod 0600 /etc/slurm/slurmdbd.conf

EXPOSE 6817 6818 6819 6820 3306 6001 6002

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
# define command at startup
ENTRYPOINT ["/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
WORKDIR /workspace/ebloc-broker/broker
CMD ["/bin/bash"]
