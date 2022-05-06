#!/usr/bin/env python3

import asyncio
import logging
from pathlib import Path

import quart.flask_patch  # noqa
from flask import abort, request
from quart import Quart

logging.disable(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)


app = Quart(__name__)


async def trade(msg):
    async with app.lock:
        await app.bot_trade.trade_main(msg)


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
    """Receive webhook message from the tradingview alerts."""
    if request.method != "POST":
        abort(400)

    data_msg = request.get_data(as_text=True)


def main():
    app.run(host="localhost", port=8000, debug=True)
    # app.run("", port=5000, debug=False)


if __name__ == "__main__":
    main()


# #!/usr/bin/env python3

# from flask import Flask

# app = Flask(__name__)


# @app.route("/")
# def hello():
#     return "Hello World!"


# if __name__ == "__main__":
#     app.run(host="localhost", port=8000, debug=True)
