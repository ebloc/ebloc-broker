import sys

from solc import compile_source
from web3 import HTTPProvider, Web3
from web3.contract import ConciseContract

from config import EBLOCPATH, HOME, RPC_PORT
from contractCalls.get_owner import get_owner
from contractCalls.get_providers import get_providers
from flask import Flask, render_template, request

# TODO: env should be load first
app = Flask(__name__)

# open a connection to the local ethereum node
http_provider = HTTPProvider("http://localhost:8545")
w3 = Web3(http_provider).eth


@app.route("/")
def hello_world():
    output = get_owner()
    return f"block_number={w3.blockNumber} | {sys.version} | owner={output} {RPC_PORT} {EBLOCPATH}."


@app.route("/hello")
def hello_name():
    _dict = get_providers()  # {'phy':50,'che':60,'maths':70}
    return render_template("hello.html", blockNumber=str(w3.blockNumber), result=dict, len=len(_dict))


"""
@app.route('/hello/<user>')
def hello_name(user):
   return render_template('hello.html', name = user)
"""
