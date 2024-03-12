#!/usr/bin/env python3

"""
curl 'https://certify.bloxberg.org/createBloxbergCertificate' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Cache-Control: no-cache' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -H 'Origin: https://certify.bloxberg.org' \
  -H 'Pragma: no-cache' \
  -H 'Referer: https://certify.bloxberg.org/' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36' \
  -H 'api_key: 6575b56b-17ab-4cc9-a16b-d499028feee9' \
  -H 'sec-ch-ua: "Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"' \
  --data-raw '{"publicKey":"0x29e613B04125c16db3f3613563bFdd0BA24Cb629","crid":["0xabcd"],"cridType":"sha2-256","enableIPFS":false,"metadataJson":"{\"authorName\":\"alper\",\"researchTitle\":\"\",\"emailAddress\":\"alper@github.com\"}"}' \
  --compressed
"""

from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit
from broker.lib import run


def main():
    json = '{"publicKey":"0x29e613B04125c16db3f3613563bFdd0BA24Cb629","crid":["0xabcd"],"cridType":"sha2-256","enableIPFS":false,"metadataJson":"{"authorName":"alper","researchTitle":"","emailAddress":"alper@github.com"}"}'
    cmd = [
        "curl",
        "https://certify.bloxberg.org/createBloxbergCertificate",
        "-H",
        "Accept: application/json, text/plain, */*",
        "-H",
        "Content-Type: application/json;charset=UTF-8",
        "-H",
        "Origin: https://certify.bloxberg.org",
        "-H",
        "Referer: https://certify.bloxberg.org/",
        "-H",
        "api_key: 6575b56b-17ab-4cc9-a16b-d499028feee9",
        "--data-raw",
        json,
        "--compressed",
    ]
    output = run(cmd)
    print(output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
