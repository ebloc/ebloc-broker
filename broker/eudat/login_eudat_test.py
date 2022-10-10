#!/usr/bin/env python3
from broker import config
from broker.config import env
from broker.libs import eudat

eudat.login(env.OC_USER, env.LOG_DIR.joinpath(".eudat_client.txt"), env.OC_CLIENT)
oc = config.oc
print("running: `oc.list('.')`")
_list = oc.list(".")
for item in _list:
    print(item)

# for item in _list:
#     print(item)
#     try:
#         oc.delete(item.path)
#     except Exception as e:
#         print(e)
