#!/usr/bin/env python3

import asyncio
import logging
import quart.flask_patch  # noqa
from contextlib import suppress
from flask import abort, request
from quart import Quart

from broker import cfg

logging.disable(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)


Ebb = cfg.Ebb
app = Quart(__name__)
owner = Ebb.get_owner()


@app.before_serving
async def startup():
    app.lock = asyncio.Lock()
    app.alertlock = asyncio.Lock()
    print(" * s t a r t i n g")


@app.route("/")
async def notify():
    return "OK"


@app.route("/webhook", methods=["POST"])
async def webhook():
    """Receive webhook message from eblocbroker.duckdns.org/oauth-redirect.php."""
    if request.method != "POST":
        abort(400)

    try:
        data_msg = request.get_data(as_text=True)
        if data_msg:
            data_split = data_msg.split(" ")
            account = data_split[0]
            orcid = data_split[1]
            with suppress(Exception):
                output = data_split[2]
                return f"wrong number of arguments provided extra argument: {output}"

            try:
                tx = Ebb.authenticate_orc_id(account, orcid, owner)
            except Exception as e:
                return str(e)

            return tx
        else:
            abort(401)
    except Exception as e:
        return str(e)


def main():
    app.run(host="localhost", port=8000, debug=True)


if __name__ == "__main__":
    main()
