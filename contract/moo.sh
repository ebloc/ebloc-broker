#!/bin/bash

#    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
#    return ansi_escape.sub('', string)
string="\u001b[0;1;34m0x5217bccc996858000b1f27d5c7099fb2db618be9ecb643057c34cce3a47b61d2\u001b[0;m"

input="$(cat <<EOF
#!/usr/bin/env python3
import subprocess
import re

string = subprocess.check_output (["echo","$string"]).strip().decode("utf-8")
ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
print(ansi_escape.sub("", string))
EOF
)"

str=$(echo "$input" | python3)
echo $str
