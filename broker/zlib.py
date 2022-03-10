#!/usr/bin/env python3

import binascii
import zlib

import base58

from broker import cfg


def alper(ipfs_hash) -> bytes:
    """Convert ipfs hash into bytes32 format."""
    bytes_array = base58.b58decode(ipfs_hash)
    return cfg.w3.toBytes(hexstr=binascii.hexlify(bytes_array).decode("utf-8"))


job_key = "1v12W1CJwSKE-SPFiq86pGpF74WPNRBD2"
print(alper(job_key))

# breakpoint()  # DEBUG
# decompressed = zlib.decompress(output.encode("cp1252"))
# print(decompressed)
# assert job_key == decompressed.decode()

# ipdb> output
# 'xœ3,34\n7tö*\x0fövÕ\r\x0epË,´0+p/p37\t\x0fð\x0brr1\x02\x00¤×\t¯'
# ipdb> output.decode()
# *** AttributeError: 'str' object has no attribute 'decode'
# ipdb> output.encode()
# b'x\xc5\x933,34\n7t\xc3\xb6*\x0f\xc3\xb6v\xc3\x95\r\x0ep\xc3\x8b,\xc2\xb40+p/p37\t\x0f\xc3\xb0\x0brr1\x02\x00\xc2\xa4\xc3\x97\t\xc2\xaf'
# ipdb> from broker import cfg
# ipdb>  cfg.w3.toBytes(output.encode())


# import sys
# import zlib

# text = "1v12W1CJwSKE-SPFiq86pGpF74WPNRBD2"

# # Checking size of text
# text_size = sys.getsizeof(text)
# print("\nsize of original text", text_size)

# # Compressing text
# compressed = zlib.compress(text.encode())

# # Checking size of text after compression
# csize = sys.getsizeof(compressed)
# print("\nsize of compressed text", csize)

# # Decompressing text
# decompressed = zlib.decompress(compressed)

# # Checking size of text after decompression
# dsize = sys.getsizeof(decompressed)
# print("\nsize of decompressed text", dsize)

# print("\nDifference of size= ", text_size - csize)
