import sys

from web3 import HTTPProvider, Web3

import eblocbroker.Contract as Contract
from config import env
from flask import Flask, render_template

# TODO: env should be load first
app = Flask(__name__)

# open a connection to the local ethereum node
w3 = Web3(HTTPProvider("http://localhost:8545")).eth
ebb = Contract.eblocbroker


@app.route("/")
def hello_world():
    output = ebb.get_owner()
    return f"block_number={w3.blockNumber} | {sys.version} | owner={output} {env.RPC_PORT} {env.EBLOCPATH}."


@app.route("/hello")
def hello_name():
    _dict = ebb.get_providers()  # {'phy':50,'che':60,'maths':70}
    return render_template("hello.html", blockNumber=str(w3.blockNumber), result=dict, len=len(_dict))


"""
@app.route('/hello/<user>')
def hello_name(user):
   return render_template('hello.html', name = user)
"""
