#!/bin/env/pyhon3

from libs import mongodb


def main():
    mongodb.delete_all()
    print("Success")


if __name__ == "__main__":
    main()
