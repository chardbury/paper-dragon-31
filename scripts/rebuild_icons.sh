#!/bin/bash

set -e;

cd "$(dirname "${BASH_SOURCE}")"/..;

SOURCE_IMAGE="data/icons/icon.png"
ICONSET_DIRECTORY_PATH="data/icons/icon.iconset"
ICNS_FILE_PATH="data/icons/icon.icns"
ICO_FILE_PATH="data/icons/icon.ico"

if ! which convert; then
    echo 'imagemagick convert utility not available; terminating';
    exit 1;
fi;

mkdir -p "${ICONSET_DIRECTORY_PATH}";

convert "${SOURCE_IMAGE}" -resize 16x16 "${ICONSET_DIRECTORY_PATH}"/icon_16x16.png;
convert "${SOURCE_IMAGE}" -resize 32x32 "${ICONSET_DIRECTORY_PATH}"/icon_16x16@2x.png;
convert "${SOURCE_IMAGE}" -resize 32x32 "${ICONSET_DIRECTORY_PATH}"/icon_32x32.png;
convert "${SOURCE_IMAGE}" -resize 64x64 "${ICONSET_DIRECTORY_PATH}"/icon_32x32@2x.png;
convert "${SOURCE_IMAGE}" -resize 64x64 "${ICONSET_DIRECTORY_PATH}"/icon_64x64.png;
convert "${SOURCE_IMAGE}" -resize 128x128 "${ICONSET_DIRECTORY_PATH}"/icon_64x64@2x.png;
convert "${SOURCE_IMAGE}" -resize 128x128 "${ICONSET_DIRECTORY_PATH}"/icon_128x128.png;
convert "${SOURCE_IMAGE}" -resize 256x256 "${ICONSET_DIRECTORY_PATH}"/icon_128x128@2x.png;
convert "${SOURCE_IMAGE}" -resize 256x256 "${ICONSET_DIRECTORY_PATH}"/icon_256x256.png;

if which iconutil; then
    iconutil -c icns -o "${ICNS_FILE_PATH}" "${ICONSET_DIRECTORY_PATH}";
else
    echo 'iconutil not available; not generating .icns file';
fi;

convert \
    "${ICONSET_DIRECTORY_PATH}"/icon_16x16.png \
    "${ICONSET_DIRECTORY_PATH}"/icon_32x32.png \
    "${ICONSET_DIRECTORY_PATH}"/icon_64x64.png \
    "${ICONSET_DIRECTORY_PATH}"/icon_128x128.png \
    "${ICONSET_DIRECTORY_PATH}"/icon_256x256.png \
    "${ICO_FILE_PATH}" \
    ;

rm -r "${ICONSET_DIRECTORY_PATH}";
