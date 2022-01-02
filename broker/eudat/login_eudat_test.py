#!/usr/bin/env python3
from broker import config
from broker.config import env
from broker.libs import eudat

eudat.login(env.OC_USER, env.LOG_PATH.joinpath(".eudat_client.txt"), env.OC_CLIENT)
oc = config.oc
print(oc.list("."))
breakpoint()  # DEBUG
