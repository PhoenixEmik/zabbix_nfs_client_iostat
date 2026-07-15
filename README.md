# Zabbix template for NFS client I/O statistics

Low-level discovery and templates for monitoring Linux NFS client performance with `nfsiostat`.

Version 1.5.0 (2026-07-15)

## Supported templates

| Zabbix version | Template | Collection mode |
| --- | --- | --- |
| 5.x and 6.x | `template_nfsio_zabbix5.xml` | One master sample with dependent items |
| 7.0+ | `template_nfsio_zabbix7.xml` | One master sample with dependent items |
| 7.0+ | `template_nfsio_zabbix7.yaml` | Same template in YAML export format |

The XML and YAML Zabbix 7 templates are alternatives. Import only one of them.

The Zabbix 5 template is expected to import on Zabbix 6, but Zabbix 6 is not currently included in automated import testing.

## Deprecated Zabbix 3 template

`template_nfsio_zabbix3.xml` is deprecated and retained only for existing installations that cannot yet upgrade. It uses the expensive legacy per-metric collection path and receives no new metrics, graphs, or other feature work. Only critical compatibility or security fixes will be considered.

New deployments should use Zabbix 5 or newer. Existing Zabbix 3 deployments should plan to upgrade and migrate to one of the dependent-item templates.

## Requirements

- Bash 4 or newer
- `nfs-utils` (`nfsiostat`)
- `util-linux` (`findmnt`)
- `jq`
- Zabbix agent or Zabbix agent 2

`UnsafeUserParameters` does not need to be enabled.

## Installation

1. Install the scripts with executable permissions:

   ```sh
   install -d -m 0755 /etc/zabbix/bin
   install -m 0755 nfsio_perf.sh nfsio_discovery.sh /etc/zabbix/bin/
   ```

2. Copy `userparameter_nfsio.conf` into a directory included by the agent configuration. Common locations are `/etc/zabbix/zabbix_agentd.d/` for the classic agent and `/etc/zabbix/zabbix_agent2.d/` for agent 2; distribution defaults vary.

3. Restart the appropriate service:

   ```sh
   systemctl restart zabbix-agent
   # or
   systemctl restart zabbix-agent2
   ```

4. Test discovery locally. Run the command as the Zabbix service account if possible:

   ```sh
   zabbix_agentd -t nfsio.discovery
   # or
   zabbix_agent2 -t nfsio.discovery
   ```

5. Import the template matching the Zabbix server version and link it to the monitored host.

## Collection design

`nfsio_discovery.sh` obtains NFS/NFSv4 mount points from `findmnt` and uses `jq` to produce escaped low-level discovery JSON. It retains the legacy `data` wrapper for the deprecated Zabbix 3 template and compatibility with existing installations.

For Zabbix 5 and newer, each discovered mount has one `nfsio.get[]` master item. One `nfsiostat` sample returns a JSON object containing all available metrics. The 22 numeric item prototypes use JSONPath preprocessing, so enabling latency, queue, retransmission, and error metrics does not launch additional `nfsiostat` processes.

The legacy `nfsio[<mount>,<metric>]` user parameter remains available for the deprecated Zabbix 3 template and manual troubleshooting. Error metrics are omitted on kernels exposing RPC iostats version 1.0; modern dependent items discard those unavailable values without becoming unsupported.

## Collected metrics

- Total operation rate and RPC backlog
- Read/write operations per second
- Read/write throughput and request size
- Read/write retransmission count and percentage
- Read/write round-trip, execution, and queue time
- Read/write error count and percentage when supported by the kernel

The modern templates include separate, unit-consistent graph prototypes for throughput, operations, request size, RPC latency, queue time, retransmissions, and errors.

## Development and validation

Run the local fixture tests:

```sh
tests/run.sh
```

The Zabbix 5 XML and Zabbix 7 XML/YAML templates are generated from a shared metric definition:

```sh
python3 scripts/generate_templates.py
python3 scripts/generate_templates.py --check
```

Template generation requires Python 3 and PyYAML. These are development dependencies only.

CI validates shell syntax and style, RPC iostats 1.0/1.1 parsing, discovery JSON escaping, generated-template consistency, XML well-formedness, and YAML syntax.

## Upgrade notes for 1.5

- Install the new `nfsio.get[*]` user parameter before importing the updated Zabbix 5/7 template.
- The updated Zabbix 5/7 templates change the existing metric prototypes to dependent items and quote mount-point key parameters.
- Review template import changes before applying them to production. Existing discovered items may be updated or recreated depending on the Zabbix version and import options.
- The Zabbix 3 template is deprecated. It remains compatible with the legacy metric interface but receives no new features.

## History

- 1.5.0 — single-sample dependent items, robust JSON and error handling, units and corrected graphs, YAML export, tests and CI; deprecated the Zabbix 3 template
- 1.4 — empty LLD response when no NFS mounts exist
- 1.3 — queue/error metrics and Zabbix 5/7 templates
- 1.2 — interval statistics instead of statistics since mount time
- 1.1 — throughput, operation-rate, and RPC graphs
- 1.0 — initial release

## Credits

This repository is derived from:

- [pdacity/zabbix_nfs_client_iostat](https://github.com/pdacity/zabbix_nfs_client_iostat)
- [yumaojun03/zabbix_monitor](https://github.com/yumaojun03/zabbix_monitor)
