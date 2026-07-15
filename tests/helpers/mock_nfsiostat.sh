#!/usr/bin/env bash

set -u

[[ -n "${NFSIOSTAT_FIXTURE:-}" ]] || exit 1
exec /usr/bin/cat "$NFSIOSTAT_FIXTURE"
