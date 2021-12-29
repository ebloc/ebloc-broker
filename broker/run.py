#!/usr/bin/env python3

from broker._utils.tools import run
while True:
    try:
        run(["gpg", "--keyserver", "hkps://keyserver.ubuntu.com", "--recv-key", "9E41B5D1F918B07E151BB8116BC2ACD088461F0A"])
    except:
        breakpoint()  # DEBUG
