#!/usr/bin/env python3

import gdown

url = "https://drive.google.com/uc?id=0B9P1L--7Wd2vNm9zMTJWOGxobkU"
output = "20150428_collected_images.tgz"
gdown.download(url, output, quiet=False)

md5 = "fa837a88f0c40c513d975104edf3da17"
gdown.cached_download(url, output, md5=md5, postprocess=gdown.extractall)

# https://drive.google.com/file/d/1zo4BkS8wqqbc7gxYQMedhqCiQUb51LAp/view?usp=sharing

gdown.download()

utils.cd("")
cmd = [
    "curl",
    "--fail",
    "-X",
    "PUT",
    "-H",
    "Content-Type: text/plain",
    "-H",
    "Authorization: Basic UVpIbzExenJzUHRyeHR2Og==",
    "--data-binary",
    "@patch_12dcd17f88086a2927aeb74d3196207b0cc4d51f_8a847d5d7581245bf48fdefe1edc89c3_0.diff.gz",
    "https://b2drop.eudat.eu/public.php/webdav/patch_12dcd17f88086a2927aeb74d3196207b0cc4d51f_8a847d5d7581245bf48fdefe1edc89c3_0.diff.gz",
    "-w",
    "%{http_code}",
]
