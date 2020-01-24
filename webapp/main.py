import sys, os
from flask import Flask, request, render_template
from solc import compile_source
from web3 import Web3, HTTPProvider
from web3.contract import ConciseContract

sys.path.insert(1, os.path.join(sys.path[0], ".."))
from contractCalls.getOwner import getOwner
from contractCalls.getClusterAddresses import getClusterAddresses

from flask import Flask

app = Flask(__name__)

# open a connection to the local ethereum node
http_provider = HTTPProvider("http://localhost:8545")
eth_provider = Web3(http_provider).eth


@app.route("/")
def hello_world():
    ret = getOwner()
    return "BlockNumber=" + str(eth_provider.blockNumber) + "|" + sys.version + "|" + ret


"""
@app.route('/hello/<user>')
def hello_name(user):
   return render_template('hello.html', name = user)
"""


@app.route("/hello")
def hello_name():
    dictt = getClusterAddresses()  # {'phy':50,'che':60,'maths':70}
    return render_template(
        "hello.html", blockNumber=str(eth_provider.blockNumber), result=dictt, len=len(dictt),
    )
