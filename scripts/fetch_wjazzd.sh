#!/bin/sh
set -eu

WJAZZD_URL="${WJAZZD_URL:-https://jazzomat.hfm-weimar.de/download/downloads/wjazzd.db}"
DEST="/data/wjazzd.db"

echo "Downloading Weimar Jazz Database from ${WJAZZD_URL}..."
curl -fSL -o "$DEST" "$WJAZZD_URL"
echo "Saved to ${DEST}."
