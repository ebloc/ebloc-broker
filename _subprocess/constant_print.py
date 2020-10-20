#!/usr/bin/env python3

from subprocess import PIPE, CalledProcessError, Popen

from utils import run_with_output

output = run_with_output(["ipfs", "add", "--progress", "--quiet", "/home/alper/alp0.txt"])
print("alper" + output)
