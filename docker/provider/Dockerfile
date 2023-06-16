FROM eblocbroker/app:latest
WORKDIR /workspace/ebloc-broker
RUN git fetch --all --quiet >/dev/null 2>&1 \
 && git pull --all -r -v >/dev/null 2>&1 \
 && pip install --disable-pip-version-check -e . --use-deprecated=legacy-resolver \
 && eblocbroker init --base \
 && eblocbroker >/dev/null 2>&1 \
 && ./broker/_utils/yaml.py >/dev/null 2>&1
