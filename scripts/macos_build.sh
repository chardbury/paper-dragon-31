#!/bin/bash

set -e;

cd "$(dirname "${BASH_SOURCE}")"/..;

venv/bin/pip install -e .[development];

APPLICATION_NAME="$(venv/bin/python -c "import applib.constants; print(applib.constants.APPLICATION_NAME);")"

venv/bin/pyi-makespec \
    --onedir --windowed --noupx \
    --add-data data:data \
    --icon data/icons/icon.icns \
    --name "${APPLICATION_NAME}" \
    scripts/pyinstaller_start.py;

venv/bin/pyinstaller --noconfirm "${APPLICATION_NAME}.spec";

rm "${APPLICATION_NAME}.spec";
