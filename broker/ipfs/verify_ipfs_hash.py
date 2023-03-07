#!/usr/bin/env python3

import multihash
import hashlib

"""
# https://github.com/ivilata/pymultihash/issues/12#issuecomment-1460187266

That Qm… string looks like a base58-encoded multihash, so you first need to
decode it into a Multihash instance, then you may use it to verify data.  For
instance:
"""


def main():
    # data = "foo"
    # print(hashlib.sha1(data))
    mh = multihash.decode(b"QmRJzsvyCQyizr73Gmms8ZRtvNxmgqumxc2KUp71dfEmoj", "base58")  # hash of b'foo'
    print(mh.verify(b"foo"))
    print(mh.verify(b"foo bar"))


if __name__ == "__main__":
    main()
