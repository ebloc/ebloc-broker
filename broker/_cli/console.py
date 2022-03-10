#!/usr/bin/env python3

from __future__ import print_function

import sys
import threading

from vulcano.app import VulcanoApp
from vulcano.app.lexer import MonokaiTheme

from broker import cfg
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker._utils.web3_tools import get_tx_status
from broker.eblocbroker_scripts.register_provider import register_provider_wrapper
from broker.eblocbroker_scripts.timenow import print_timenow
from broker.errors import QuietExit
from broker.submit_base import SubmitBase


def my_inline_function():
    cfg.Ebb.get_block_number()  # starts as thread right away


app = VulcanoApp()
Ebb = cfg.Ebb
t1 = threading.Thread(target=my_inline_function)
t1.start()


def has_context_name():
    """Function to hide a command from command line

    This function is to prevent showing help and autocomplete for commands that need the name
    to be set up on the context.
    """
    return "name" in app.context


@app.command("balance", "Returns user's earned money amount in Wei.")
def balance(eth_address):
    """Return block number.

    :param str eth_address: Ethereum address of the provider
    """
    t1.join()
    balance = Ebb.get_balance(eth_address)
    log(f"## balance={balance}")


@app.command("block_number", "Returns block number")
def block_number():
    """Return block number."""
    t1.join()
    log(f"block_number={Ebb.get_block_number()}", "bold")


@app.command("owner", "Returns owner")
def get_owner():
    """Return owner of the contract."""
    t1.join()
    log(Ebb.get_owner().lower(), "bold")


@app.command("is_web3_connected", "Returns web3 status")
def is_web3_connected():
    """Return block number."""
    t1.join()
    log(Ebb.is_web3_connected())


@app.command("providers", "Returns registered providers")
def get_providers():
    """Return block number."""
    t1.join()
    log(Ebb.get_providers())


@app.command("list_registered_data_files", "Returns registered data files of the provider")
def list_registered_data_files(eth_address):
    """Return registered data files of the given provider.

    :param str eth_address: Ethereum address of the provider
    """
    t1.join()
    try:
        cfg.Ebb.get_data_info(eth_address)
    except Exception as e:
        print_tb(e)


@app.command("provider_info", "Returns provider info")
def get_provider_info(address):
    """Return provider info.

    :param str address: Ethereum address of the provider
    """
    t1.join()
    log(Ebb.get_provider_info(address))


@app.command("requester_info", "Returns requester info")
def get_requester_info(address):
    """Return provider info.

    :param str address: Ethereum address of the provider
    """
    t1.join()
    log(Ebb.get_requester_info(address))


@app.command("timenow", "Returns Bloxberg's signer node's time")
def _timenow():
    t1.join()
    print_timenow()


@app.command("register_requester", "Registers requester info")
def register_requester(yaml_fn):
    """Return provider info.

    :param str yaml_fn: Full file path of Yaml file that contains the requester info
    """
    t1.join()
    try:
        tx_hash = Ebb.register_requester(yaml_fn)
        if tx_hash:
            get_tx_status(tx_hash)
        else:
            log()
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


@app.command("register_provider", "Registers provider info")
def register_provider(yaml_fn):
    """Return provider info.

    :param str yaml_fn: Full file path of Yaml file that contains the provider info
    """
    t1.join()
    try:
        register_provider_wrapper(yaml_fn)
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


@app.command("submit", "Submits job")
def submit_job(yaml_fn):
    """Return provider info.

    :param str yaml_fn: Full file path of Yaml file that contains the job info
    """
    t1.join()
    try:
        base = SubmitBase(yaml_fn)
        base.submit()
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


# @app.command("hi", "Salute people given form parameter")
# def salute_method_here(name, title="Mr."):
#     """Salute to someone

#     :param str address: Name of who you want to say hi!
#     :param str title: Title of this person
#     """
#     print("Hi! {} {} :) Glad to see you.".format(title, name))


# @app.command
# def i_am(name):
#     """Set your name

#     :param str name: Your name goes here!
#     """
#     app.context["name"] = name


# @app.command(show_if=has_context_name)
# def whoami():
#     """Returns your name from the context

#     This is only shown where you've set your name
#     """
#     return app.context["name"]


# @app.command
# def bye(name="User"):
#     """Say goodbye to someone"""
#     return "Bye {}!".format(name)


# @app.command
# def sum_numbers(*args):
#     """Sums all numbers passed as parameters"""
#     return sum(args)


# @app.command
# def multiply(number1, number2):
#     """Just multiply two numbers"""
#     return number1 * number2


# @app.command
# def reverse_word(word):
#     """Reverse a word"""
#     return word[::-1]


# @app.command
# def random_upper_word(word):
#     """Returns the word with random upper letters"""
#     return "".join(random.choice([letter.upper(), letter]) for letter in word)


def python_console():
    app.run(theme=MonokaiTheme)


if __name__ == "__main__":
    try:
        python_console()
    except KeyboardInterrupt:
        sys.exit(1)
