#!/bin/bash

rm contracts/.\#Lib.sol
brownie compile
brownie test
