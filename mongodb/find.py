#!/bin/env/python3

from libs import mongodb

mongodb.find_all()

print("----")

requesterID = "0x12ba09353d5C8aF8Cb362d6FF1D782C1E195b571"
key = "Qmamk5qqSd9oT465sGtZvn4jeR5jXeJADQuARVfkaxfGQL"

if mongodb.is_received(requesterID, key, 0, True):
    print("yes")

v = mongodb.get_job_block_number(requesterID, key, 0)
print(v)
