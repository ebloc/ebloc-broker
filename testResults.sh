#!/bin/bash

readFrom=1810340;
clusterID="0xcc8de90b4ada1c67d68c1958617970308e4ee75e";

node log.js  $readFrom $clusterID
node log1.js $readFrom $clusterID
node main.js $clusterID
