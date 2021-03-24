#!/bin/bash

set -e;

cd "$(dirname "${0}")"/..;

[[ -f venv/bin/activate ]] || python3.9 -m venv venv;

venv/bin/python -m pip install -U pip;

venv/bin/pip install -e .[development];

source venv/bin/activate;

exec bash;