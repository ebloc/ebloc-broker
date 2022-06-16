#!/usr/bin/env python3

"""Convert Markdown to reStructuredText extension for Sphinx Doc

Scans for '.md' files and converts them to '.rst' files using pandoc.

For use it just copy this file to your source directory and add
'convert_md_2_rst' to the 'extensions' value of your 'conf.py' file.

Ensure that the source path is in the Python sys path. For that
purpose you may add this line to 'conf.py':

sys.path.insert(0, os.path.abspath('.'))
"""

import os
from os.path import expanduser

import pypandoc


def setup(app):
    path = os.path.abspath(".") + "/source"
    for dir, subdir, files in os.walk(path):
        for file in files:
            fn = os.path.join(dir, file)
            fn_parts = os.path.splitext(fn)
            if len(fn_parts) > 1:
                fn_ext = fn_parts[1]
                if fn_ext == ".md":
                    convert_md_2_rst_process(fn_parts[0])


def convert_md_2_rst_process(fn_root):
    fn_source = fn_root + ".md"
    fn_target = fn_root + ".rst"
    print(
        "Converting",
        os.path.basename(fn_source),
        "to",
        os.path.basename(fn_target),
    )
    file_source = open(fn_source)
    lines = file_source.readlines()

    for i in range(0, len(lines)):
        lines[i] = lines[i].rstrip()

    file_source.close()
    data = "\n".join(lines)
    data = data.encode("utf-8")
    data = pypandoc.convert(data, "rst", format="markdown")
    file_target = open(fn_target, "w")
    file_target.write(data)
    file_target.flush()
    file_target.close()


setup(f"{expanduser('~')}/ebloc-broker/docs/convert")
