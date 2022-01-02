#!/bin/bash

base_url='https://orcid.org/oauth/authorize?client_id='
client_id='APP-90R3NMFJNN5M4J84'
redirect_uri='http://ebloc.org';
echo $base_url$client_id'&response_type=code&scope=/authenticate&redirect_uri='$redirect_uri''
