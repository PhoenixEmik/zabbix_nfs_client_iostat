#!/usr/bin/env bash

set -u
set -o pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PERF="$ROOT/nfsio_perf.sh"
DISCOVERY="$ROOT/nfsio_discovery.sh"
MOCK_FINDMNT="$ROOT/tests/helpers/mock_findmnt.sh"
MOCK_NFSIOSTAT="$ROOT/tests/helpers/mock_nfsiostat.sh"
FIXTURE_V11="$ROOT/tests/fixtures/nfsiostat_v1_1.txt"
FIXTURE_V10="$ROOT/tests/fixtures/nfsiostat_v1_0.txt"

tests_run=0

fail() {
    printf 'not ok %d - %s\n' "$tests_run" "$*" >&2
    exit 1
}

pass() {
    printf 'ok %d - %s\n' "$tests_run" "$1"
}

run_test() {
    tests_run=$((tests_run + 1))
    "$@"
}

test_v11_json() {
    local output
    output=$(FINDMNT_BIN="$MOCK_FINDMNT" NFSIOSTAT_BIN="$MOCK_NFSIOSTAT" \
        NFSIOSTAT_FIXTURE="$FIXTURE_V11" "$PERF" '/mock nfs') || \
        fail 'RPC iostats 1.1 collection failed'
    jq -e '
        length == 22 and
        keys == [
            "bklog", "op_s",
            "read_error", "read_error_perc", "read_exe", "read_kB_op", "read_kB_s", "read_ops_s",
            "read_queue", "read_retry", "read_retry_perc", "read_rtt",
            "write_error", "write_error_perc", "write_exe", "write_kB_op", "write_kB_s", "write_ops_s",
            "write_queue", "write_retry", "write_retry_perc", "write_rtt"
        ] and
        .op_s == 12.345 and
        .read_retry_perc == 5.5 and
        .write_ops_s == 4.5 and
        .write_error_perc == 3.5
    ' <<< "$output" >/dev/null || fail 'RPC iostats 1.1 JSON values are incorrect'
    pass 'collect all RPC iostats 1.1 metrics as JSON'
}

test_legacy_metric() {
    local output
    output=$(FINDMNT_BIN="$MOCK_FINDMNT" NFSIOSTAT_BIN="$MOCK_NFSIOSTAT" \
        NFSIOSTAT_FIXTURE="$FIXTURE_V11" "$PERF" '/mock nfs' write_ops_s) || \
        fail 'legacy metric collection failed'
    [[ "$output" == "4.500" ]] || fail "unexpected legacy value: $output"
    pass 'preserve the legacy per-metric interface'
}

test_v10_optional_metrics() {
    local output
    output=$(FINDMNT_BIN="$MOCK_FINDMNT" NFSIOSTAT_BIN="$MOCK_NFSIOSTAT" \
        NFSIOSTAT_FIXTURE="$FIXTURE_V10" "$PERF" '/mock nfs') || \
        fail 'RPC iostats 1.0 collection failed'
    jq -e 'length == 18 and (has("read_error") | not) and (has("write_error_perc") | not)' \
        <<< "$output" >/dev/null || fail 'optional error fields were not omitted'
    if FINDMNT_BIN="$MOCK_FINDMNT" NFSIOSTAT_BIN="$MOCK_NFSIOSTAT" \
        NFSIOSTAT_FIXTURE="$FIXTURE_V10" "$PERF" '/mock nfs' read_error >/dev/null 2>&1; then
        fail 'unavailable error metric unexpectedly succeeded'
    fi
    pass 'support RPC iostats 1.0 without inventing error values'
}

test_invalid_inputs() {
    if "$PERF" >/dev/null 2>&1; then
        fail 'missing arguments unexpectedly succeeded'
    fi
    if FINDMNT_BIN="$MOCK_FINDMNT" NFSIOSTAT_BIN="$MOCK_NFSIOSTAT" \
        NFSIOSTAT_FIXTURE="$FIXTURE_V11" "$PERF" '/mock nfs' unknown >/dev/null 2>&1; then
        fail 'unknown metric unexpectedly succeeded'
    fi
    if MOCK_FSTYPE=xfs FINDMNT_BIN="$MOCK_FINDMNT" NFSIOSTAT_BIN="$MOCK_NFSIOSTAT" \
        NFSIOSTAT_FIXTURE="$FIXTURE_V11" "$PERF" /mock >/dev/null 2>&1; then
        fail 'non-NFS mount unexpectedly succeeded'
    fi
    pass 'reject unknown metrics and non-NFS mounts'
}

test_discovery_escaping() {
    local output input
    input='{"filesystems":[{"target":"/mnt/space and \"quote\""},{"target":"/mnt/back\\slash"}]}'
    output=$(MOCK_FINDMNT_JSON="$input" FINDMNT_BIN="$MOCK_FINDMNT" JQ_BIN=/usr/bin/jq \
        "$DISCOVERY") || fail 'special-character discovery failed'
    jq -e '
        .data | length == 2 and
        .[0]["{#MOUNT_POINT}"] == "/mnt/space and \"quote\"" and
        .[1]["{#MOUNT_POINT}"] == "/mnt/back\\slash"
    ' <<< "$output" >/dev/null || fail 'mount names were not JSON escaped correctly'
    pass 'serialize special characters in mount names'
}

test_empty_discovery() {
    local output
    output=$(MOCK_FINDMNT_EMPTY=1 FINDMNT_BIN="$MOCK_FINDMNT" JQ_BIN=/usr/bin/jq \
        "$DISCOVERY") || fail 'empty discovery failed'
    jq -e '. == {"data":[]}' <<< "$output" >/dev/null || fail 'empty discovery result is incorrect'
    pass 'return an empty LLD array when no NFS mounts exist'
}

printf '1..6\n'
run_test test_v11_json
run_test test_legacy_metric
run_test test_v10_optional_metrics
run_test test_invalid_inputs
run_test test_discovery_escaping
run_test test_empty_discovery
