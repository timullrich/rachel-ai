#!/usr/bin/env bash
set -euo pipefail

RUNTIME_PATH="/opt/plugins/gtaf-runtime"
SDK_PATH="/opt/plugins/gtaf-sdk-py"

if [ -d "$RUNTIME_PATH" ]; then
  pip install -e "$RUNTIME_PATH" >/tmp/gtaf-runtime-install.log 2>&1 || {
    cat /tmp/gtaf-runtime-install.log
    exit 1
  }
fi

if [ -d "$SDK_PATH" ]; then
  pip install -e "$SDK_PATH" --no-deps >/tmp/gtaf-sdk-install.log 2>&1 || {
    cat /tmp/gtaf-sdk-install.log
    exit 1
  }
fi

exec "$@"
