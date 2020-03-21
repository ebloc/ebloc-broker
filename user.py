#!/usr/bin/env python3

import pwd


def username_check(check):
    """Check if username exists."""

    try:
        pwd.getpwnam(check)
        print("USER %s EXISTS. TRY A DIFFERENT USERNAME." % (check))
        return False

    except KeyError:
        print("User %s does not exist. Continuing... %s" % (check, check))
        return True


success = username_check("alper1k")

if not success:
    print("here")
