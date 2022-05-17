#!/usr/bin/env python3

import logging

import quart.flask_patch  # noqa
from flask import abort, request
from quart import Quart

from broker import cfg

logging.disable(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

Ebb = cfg.Ebb
app = Quart(__name__)


async def trade(msg):
    async with app.lock:
        await app.bot_trade.trade_main(msg)


@app.before_serving
async def startup():
    print(" * s t a r t i n g")


@app.route("/")
async def notify():
    return "OK"


@app.route("/webhook", methods=["POST"])
async def webhook():
    if request.method != "POST":
        abort(400)

    data_msg = request.get_data(as_text=True)
    if data_msg:
        print(Ebb.get_block_number())
        # await trade(data_msg.replace(":00Z", "").rstrip())
        return "OK", 200
    else:
        abort(403)


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
