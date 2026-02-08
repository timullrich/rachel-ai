#!/usr/bin/env bash
set -euo pipefail

PLUGIN_PATH="/opt/plugins/gtaf-runtime"

if [ -d "$PLUGIN_PATH" ]; then
  pip install "$PLUGIN_PATH" >/tmp/gtaf-runtime-install.log 2>&1 || {
    cat /tmp/gtaf-runtime-install.log
    exit 1
  }
fi

exec "$@"
