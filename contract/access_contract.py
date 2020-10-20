#!/bin/env/pyhon3

from brownie import network, project
from brownie.project.Ebb import *

p = project.load('/home/alper/eBlocBroker/contract', name="Ebb")
p.load_config()


network.connect('private')
p = project.Ebb
print(p.eBlocBroker)
