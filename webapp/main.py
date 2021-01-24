#!/usr/bin/env python3

import config
from flask import Flask, render_template

# Settings
app = Flask(__name__)
app.config.from_pyfile("settings.py")


@app.route("/")
def index():
    print(config.Ebb.get_owner())
    return app.config.get("WHOAMI")


# home route
@app.route("/")
def hello():
    # index()
    return render_template("index.html", name=app.config.get("WHOAMI"), block_number=config.Ebb.get_block_number())


if __name__ == "__main__":
    app.run(debug=True)
