FROM eblocbroker/app:latest
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY supervisord.conf /etc/
# RUN unlink /var/run/supervisor/supervisor.sock

# ENTRYPOINT ["/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
