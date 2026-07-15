#!/usr/bin/env bash

set -u

for argument in "$@"; do
    if [[ "$argument" == "--json" ]]; then
        if [[ "${MOCK_FINDMNT_EMPTY:-0}" == "1" ]]; then
            exit 1
        fi
        if [[ -n "${MOCK_FINDMNT_JSON:-}" ]]; then
            printf '%s\n' "$MOCK_FINDMNT_JSON"
        else
            printf '%s\n' '{"filesystems":[{"target":"/mock nfs"}]}'
        fi
        exit "${MOCK_FINDMNT_EXIT:-0}"
    fi
done

if [[ "${MOCK_FINDMNT_EXIT:-0}" != "0" ]]; then
    exit "$MOCK_FINDMNT_EXIT"
fi

printf '%s\n' "${MOCK_FSTYPE:-nfs4}"
