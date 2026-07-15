#!/usr/bin/env bash

set -u
set -o pipefail

FINDMNT_BIN=${FINDMNT_BIN:-/usr/bin/findmnt}
JQ_BIN=${JQ_BIN:-/usr/bin/jq}

fail() {
    printf 'nfsio discovery: %s\n' "$*" >&2
    exit 1
}

[[ -x "$FINDMNT_BIN" ]] || fail "findmnt is not executable: $FINDMNT_BIN"
[[ -x "$JQ_BIN" ]] || fail "jq is not executable: $JQ_BIN"

# findmnt performs the filesystem-name escaping and jq performs the JSON/LLD
# serialization. The legacy data wrapper keeps the output compatible with
# Zabbix 3 while remaining accepted by newer Zabbix versions.
mounts_json=$(
    "$FINDMNT_BIN" --json --list --types nfs,nfs4 --output TARGET 2>&1
) || {
    if [[ -z "${mounts_json:-}" ]]; then
        mounts_json='{"filesystems":[]}'
    else
        fail "unable to read the NFS mount table: $mounts_json"
    fi
}

[[ -n "$mounts_json" ]] || mounts_json='{"filesystems":[]}'

"$JQ_BIN" --compact-output \
    '{data: [(.filesystems // [])[] | {"{#MOUNT_POINT}": .target}]}' \
    <<< "$mounts_json" || fail 'findmnt returned invalid JSON'
