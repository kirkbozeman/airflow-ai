#!/usr/bin/env bash
set -euo pipefail

DWH_DSN="${DWH_DSN:-postgresql://dwh:dwh@dwh:5432/dwh}"
SRC="/data/wjazzd.db"

echo "Loading ${SRC} into ${DWH_DSN}..."
pgloader "$SRC" "$DWH_DSN"

echo "Done."
