#!/usr/bin/env bash

set -u
set -o pipefail

NFSIOSTAT_BIN=${NFSIOSTAT_BIN:-/usr/sbin/nfsiostat}
FINDMNT_BIN=${FINDMNT_BIN:-/usr/bin/findmnt}

readonly -a METRICS=(
    op_s bklog
    read_ops_s read_kB_s read_kB_op read_retry read_retry_perc
    read_rtt read_exe read_queue read_error read_error_perc
    write_ops_s write_kB_s write_kB_op write_retry write_retry_perc
    write_rtt write_exe write_queue write_error write_error_perc
)

fail() {
    printf 'nfsio: %s\n' "$*" >&2
    exit 1
}

usage() {
    printf 'Usage: %s <NFS mount point> [metric]\n' "${0##*/}" >&2
    exit 2
}

is_known_metric() {
    local candidate=$1 metric

    for metric in "${METRICS[@]}"; do
        [[ "$candidate" == "$metric" ]] && return 0
    done

    return 1
}

[[ $# -ge 1 && $# -le 2 ]] || usage

mount_point=$1
requested_metric=${2:-}

[[ -n "$mount_point" ]] || fail 'mount point must not be empty'
[[ -z "$requested_metric" ]] || is_known_metric "$requested_metric" || \
    fail "unsupported metric: $requested_metric"
[[ -x "$NFSIOSTAT_BIN" ]] || fail "nfsiostat is not executable: $NFSIOSTAT_BIN"
[[ -x "$FINDMNT_BIN" ]] || fail "findmnt is not executable: $FINDMNT_BIN"

filesystem_type=$(
    "$FINDMNT_BIN" --noheadings --mountpoint "$mount_point" --output FSTYPE 2>/dev/null
) || fail "not an active mount point: $mount_point"

filesystem_type=${filesystem_type%%$'\n'*}
case "$filesystem_type" in
    nfs|nfs4) ;;
    *) fail "not an NFS mount point: $mount_point" ;;
esac

raw_output=$(
    LC_ALL=C "$NFSIOSTAT_BIN" 1 2 -- "$mount_point"
) || fail "nfsiostat failed for mount point: $mount_point"

parsed_output=$(
    awk '
        function clean_percent(value) {
            gsub(/[()%]/, "", value)
            return value
        }

        /rpc bklog/ {
            section = "summary"
            next
        }

        /^read:/ {
            section = "read"
            next
        }

        /^write:/ {
            section = "write"
            next
        }

        section == "summary" && NF >= 2 {
            op_s = $1
            bklog = $2
            have_summary = 1
            section = ""
            next
        }

        section == "read" && NF >= 8 {
            read_ops_s = $1
            read_kB_s = $2
            read_kB_op = $3
            read_retry = $4
            read_retry_perc = clean_percent($5)
            read_rtt = $6
            read_exe = $7
            read_queue = $8
            read_error = (NF >= 10 ? $9 : "")
            read_error_perc = (NF >= 10 ? clean_percent($10) : "")
            have_read = 1
            section = ""
            next
        }

        section == "write" && NF >= 8 {
            write_ops_s = $1
            write_kB_s = $2
            write_kB_op = $3
            write_retry = $4
            write_retry_perc = clean_percent($5)
            write_rtt = $6
            write_exe = $7
            write_queue = $8
            write_error = (NF >= 10 ? $9 : "")
            write_error_perc = (NF >= 10 ? clean_percent($10) : "")
            have_write = 1
            section = ""
            next
        }

        END {
            if (!have_summary || !have_read || !have_write)
                exit 1

            print "op_s=" op_s
            print "bklog=" bklog
            print "read_ops_s=" read_ops_s
            print "read_kB_s=" read_kB_s
            print "read_kB_op=" read_kB_op
            print "read_retry=" read_retry
            print "read_retry_perc=" read_retry_perc
            print "read_rtt=" read_rtt
            print "read_exe=" read_exe
            print "read_queue=" read_queue
            if (read_error != "") {
                print "read_error=" read_error
                print "read_error_perc=" read_error_perc
            }
            print "write_ops_s=" write_ops_s
            print "write_kB_s=" write_kB_s
            print "write_kB_op=" write_kB_op
            print "write_retry=" write_retry
            print "write_retry_perc=" write_retry_perc
            print "write_rtt=" write_rtt
            print "write_exe=" write_exe
            print "write_queue=" write_queue
            if (write_error != "") {
                print "write_error=" write_error
                print "write_error_perc=" write_error_perc
            }
        }
    ' <<< "$raw_output"
) || fail 'unable to parse nfsiostat output'

declare -A values=()
while IFS='=' read -r name value; do
    [[ -n "$name" ]] || continue
    [[ "$value" =~ ^-?[0-9]+([.][0-9]+)?$ ]] || \
        fail "nfsiostat returned a non-numeric value for $name"
    values["$name"]=$value
done <<< "$parsed_output"

if [[ -n "$requested_metric" ]]; then
    [[ -n "${values[$requested_metric]+present}" ]] || \
        fail "metric is unavailable on this kernel: $requested_metric"
    printf '%s\n' "${values[$requested_metric]}"
    exit 0
fi

separator=
printf '{'
for metric in "${METRICS[@]}"; do
    [[ -n "${values[$metric]+present}" ]] || continue
    printf '%s"%s":%s' "$separator" "$metric" "${values[$metric]}"
    separator=,
done
printf '}\n'
