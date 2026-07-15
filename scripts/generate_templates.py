#!/usr/bin/env python3
"""Generate the Zabbix 5 XML and Zabbix 7 XML/YAML templates."""

import argparse
import datetime as dt
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_NAME = "Template NFS IO Stats"
MASTER_KEY = 'nfsio.get["{#MOUNT_POINT}"]'
RELEASE_DATE = "2026-07-15T00:00:00Z"

GROUP_UUID = "7df96b18c230490a9a0a9e2307226338"
TEMPLATE_UUID = "408d615ff22d40f4a2572cc011f8903d"
DISCOVERY_UUID = "0000266c4f934139a9c0e96c9068a40e"
MASTER_UUID = "6a1e4fcf9e4a4bb9a7de28c884f41101"

METRICS = [
    {
        "key": "bklog",
        "uuid": "2ebc7f237cfa40d1bcfb2d4cebecff2d",
        "label": "RPC backlog",
        "unit": "",
        "description": "Average length of the RPC backlog queue.",
    },
    {
        "key": "op_s",
        "uuid": "2649c5720097410192c860a3cfbf9bf6",
        "label": "Operations",
        "unit": "ops/s",
        "description": "Total NFS RPC operations per second.",
    },
    {
        "key": "read_error",
        "uuid": "0f805a66c2a04e48a8acf1368bf111e5",
        "label": "Read errors",
        "unit": "errors",
        "description": "Read operations completed with an error during the sample interval. Available with RPC iostats version 1.1 or newer.",
        "optional": True,
    },
    {
        "key": "read_error_perc",
        "uuid": "75119e1dbb4543baa443cba2cb2eaa02",
        "label": "Read error rate",
        "unit": "%",
        "description": "Percentage of read operations completed with an error. Available with RPC iostats version 1.1 or newer.",
        "optional": True,
    },
    {
        "key": "read_exe",
        "uuid": "dbcc2244995246bf9b7aef96ddaf452d",
        "label": "Read execution time",
        "unit": "ms",
        "description": "Average time to complete an RPC read request, including round-trip time.",
    },
    {
        "key": "read_kB_op",
        "uuid": "f3ef7817bac14059a53b9c6c1ce24868",
        "label": "Read request size",
        "unit": "kB/op",
        "description": "Average kilobytes read per operation.",
    },
    {
        "key": "read_kB_s",
        "uuid": "470f1840b99745399de8987b393b2eb0",
        "label": "Read throughput",
        "unit": "kB/s",
        "description": "Kilobytes read per second.",
    },
    {
        "key": "read_ops_s",
        "uuid": "63e6db20fdfe490592a2aa9ab6aa249a",
        "label": "Read operations",
        "unit": "ops/s",
        "description": "Read operations per second.",
    },
    {
        "key": "read_queue",
        "uuid": "93f1c091aa344d4c86b7ecc3a221585b",
        "label": "Read queue time",
        "unit": "ms",
        "description": "Average time an RPC read request waits before transmission.",
    },
    {
        "key": "read_retry",
        "uuid": "fbc1381c6aca4a68bcfa521687003657",
        "label": "Read retransmissions",
        "unit": "retrans",
        "description": "Read retransmissions during the sample interval.",
    },
    {
        "key": "read_retry_perc",
        "uuid": "088f87604a7548fa96f8f1056d5a103b",
        "label": "Read retransmission rate",
        "unit": "%",
        "description": "Read retransmissions as a percentage of read operations.",
    },
    {
        "key": "read_rtt",
        "uuid": "c4d76f20f67744918233c5dfd72c5940",
        "label": "Read round-trip time",
        "unit": "ms",
        "description": "Average RPC read request round-trip time.",
    },
    {
        "key": "write_error",
        "uuid": "31469835ab1c4fc6bb6a52556b84bb5d",
        "label": "Write errors",
        "unit": "errors",
        "description": "Write operations completed with an error during the sample interval. Available with RPC iostats version 1.1 or newer.",
        "optional": True,
    },
    {
        "key": "write_error_perc",
        "uuid": "a275429ccd4847ef8707d74550f0ebf2",
        "label": "Write error rate",
        "unit": "%",
        "description": "Percentage of write operations completed with an error. Available with RPC iostats version 1.1 or newer.",
        "optional": True,
    },
    {
        "key": "write_exe",
        "uuid": "da18e12fd2474b10bd94b0b46747343a",
        "label": "Write execution time",
        "unit": "ms",
        "description": "Average time to complete an RPC write request, including round-trip time.",
    },
    {
        "key": "write_kB_op",
        "uuid": "ae0c34e9a50141548559429c18757d6b",
        "label": "Write request size",
        "unit": "kB/op",
        "description": "Average kilobytes written per operation.",
    },
    {
        "key": "write_kB_s",
        "uuid": "80a1fe9747a4476d9be22d1c4420b8a4",
        "label": "Write throughput",
        "unit": "kB/s",
        "description": "Kilobytes written per second.",
    },
    {
        "key": "write_ops_s",
        "uuid": "b17595fa91ba4f80aa876f8f6b6970e3",
        "label": "Write operations",
        "unit": "ops/s",
        "description": "Write operations per second.",
    },
    {
        "key": "write_queue",
        "uuid": "93c3835b796c4da2bcb3a81661ea57cb",
        "label": "Write queue time",
        "unit": "ms",
        "description": "Average time an RPC write request waits before transmission.",
    },
    {
        "key": "write_retry",
        "uuid": "52a8bfbb904f444bac620ea8d3c4401e",
        "label": "Write retransmissions",
        "unit": "retrans",
        "description": "Write retransmissions during the sample interval.",
    },
    {
        "key": "write_retry_perc",
        "uuid": "650fd69737df4ce78d614d187ac7e4f6",
        "label": "Write retransmission rate",
        "unit": "%",
        "description": "Write retransmissions as a percentage of write operations.",
    },
    {
        "key": "write_rtt",
        "uuid": "f24f8c53a22a49cb9502f6817427e87b",
        "label": "Write round-trip time",
        "unit": "ms",
        "description": "Average RPC write request round-trip time.",
    },
]

GRAPHS = [
    {
        "uuid": "9dd49be64abf43819692e73097d962b2",
        "name": "Request size",
        "metrics": ["read_kB_op", "write_kB_op"],
    },
    {
        "uuid": "b5b2a411d05145779b9c79ff1ba8e381",
        "name": "Throughput",
        "metrics": ["read_kB_s", "write_kB_s"],
    },
    {
        "uuid": "e8cc0748f2e84e52ba221c5b7dce2d3d",
        "name": "Operations",
        "metrics": ["read_ops_s", "write_ops_s"],
    },
    {
        "uuid": "749c205dfdc64c21b082d1c9f457ad70",
        "name": "RPC latency",
        "metrics": ["read_rtt", "write_rtt", "read_exe", "write_exe"],
    },
    {
        "uuid": "a0c4c2b485dd48a8bc9563c46e0406e9",
        "name": "RPC queue time",
        "metrics": ["read_queue", "write_queue"],
    },
    {
        "uuid": "3b6e18df38f14f87a33c4ca3e45c8cc7",
        "name": "Retransmissions",
        "metrics": ["read_retry_perc", "write_retry_perc"],
    },
    {
        "uuid": "70d6e9fa94304b4da3eb14a34cfe4981",
        "name": "Errors",
        "metrics": ["read_error_perc", "write_error_perc"],
    },
]

COLORS = ["1A7C11", "F63100", "2774A4", "AA00AA"]


def item_key(metric: str) -> str:
    return f'nfsio["{{#MOUNT_POINT}}",{metric}]'


def add(parent: ET.Element, tag: str, text: Optional[str] = None) -> ET.Element:
    child = ET.SubElement(parent, tag)
    if text is not None:
        child.text = text
    return child


def indent_xml(element: ET.Element, level: int = 0) -> None:
    indentation = "\n" + level * "    "
    child_indentation = "\n" + (level + 1) * "    "
    if len(element):
        if not element.text or not element.text.strip():
            element.text = child_indentation
        if level and (not element.tail or not element.tail.strip()):
            element.tail = indentation
        for child in element:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indentation
    elif level and (not element.tail or not element.tail.strip()):
        element.tail = indentation


def add_applications(parent: ET.Element) -> None:
    applications = add(parent, "applications")
    application = add(applications, "application")
    add(application, "name", "NFS")


def add_tags(parent: ET.Element, value: str = "NFS") -> None:
    tags = add(parent, "tags")
    tag = add(tags, "tag")
    add(tag, "tag", "Application")
    add(tag, "value", value)


def add_preprocessing(parent: ET.Element, metric: Dict[str, Any]) -> None:
    preprocessing = add(parent, "preprocessing")
    step = add(preprocessing, "step")
    add(step, "type", "JSONPATH")
    parameters = add(step, "parameters")
    add(parameters, "parameter", f'$.{metric["key"]}')
    if metric.get("optional"):
        add(step, "error_handler", "DISCARD_VALUE")


def add_master_item(parent: ET.Element) -> None:
    master_item = add(parent, "master_item")
    add(master_item, "key", MASTER_KEY)


def build_xml(version: str) -> str:
    root = ET.Element("zabbix_export")
    add(root, "version", version)

    if version == "5.0":
        add(root, "date", RELEASE_DATE)
        groups = add(root, "groups")
        group = add(groups, "group")
        add(group, "name", "Templates")
    else:
        groups = add(root, "template_groups")
        group = add(groups, "template_group")
        add(group, "uuid", GROUP_UUID)
        add(group, "name", "Templates")

    templates = add(root, "templates")
    template = add(templates, "template")
    if version == "7.0":
        add(template, "uuid", TEMPLATE_UUID)
    add(template, "template", TEMPLATE_NAME)
    add(template, "name", TEMPLATE_NAME)
    add(
        template,
        "description",
        "NFS client statistics from nfsiostat. Modern templates collect all metrics once per mount and use dependent items.",
    )
    template_groups = add(template, "groups")
    template_group = add(template_groups, "group")
    add(template_group, "name", "Templates")
    if version == "5.0":
        add_applications(template)

    discovery_rules = add(template, "discovery_rules")
    discovery = add(discovery_rules, "discovery_rule")
    if version == "7.0":
        add(discovery, "uuid", DISCOVERY_UUID)
    add(discovery, "name", "NFS mount point discovery")
    add(discovery, "key", "nfsio.discovery")
    add(discovery, "delay", "2m")
    add(discovery, "lifetime", "1d")
    if version == "7.0":
        add(discovery, "enabled_lifetime_type", "DISABLE_NEVER")
    add(discovery, "description", "Discovers mounted NFS and NFSv4 filesystems.")

    prototypes = add(discovery, "item_prototypes")
    master = add(prototypes, "item_prototype")
    if version == "7.0":
        add(master, "uuid", MASTER_UUID)
    add(master, "name", "{#MOUNT_POINT}: Get NFS client statistics")
    add(master, "key", MASTER_KEY)
    add(master, "delay", "1m")
    add(master, "history", "0")
    add(master, "trends", "0")
    add(master, "value_type", "TEXT")
    add(master, "description", "Raw JSON returned by one nfsiostat sample. Used by dependent item prototypes.")
    if version == "5.0":
        add_applications(master)
    else:
        add_tags(master, "NFS raw")

    for metric in METRICS:
        prototype = add(prototypes, "item_prototype")
        if version == "7.0":
            add(prototype, "uuid", metric["uuid"])
        add(prototype, "name", f'{{#MOUNT_POINT}}: {metric["label"]}')
        add(prototype, "type", "DEPENDENT")
        add(prototype, "key", item_key(metric["key"]))
        add(prototype, "delay", "0")
        add(prototype, "history", "30d")
        add(prototype, "value_type", "FLOAT")
        if metric["unit"]:
            add(prototype, "units", metric["unit"])
        add(prototype, "description", metric["description"])
        add_preprocessing(prototype, metric)
        add_master_item(prototype)
        if version == "5.0":
            add_applications(prototype)
        else:
            add_tags(prototype)

    graph_prototypes = add(discovery, "graph_prototypes")
    for graph in GRAPHS:
        graph_prototype = add(graph_prototypes, "graph_prototype")
        if version == "7.0":
            add(graph_prototype, "uuid", graph["uuid"])
        add(graph_prototype, "name", f'{{#MOUNT_POINT}}: {graph["name"]}')
        graph_items = add(graph_prototype, "graph_items")
        for index, metric in enumerate(graph["metrics"]):
            graph_item = add(graph_items, "graph_item")
            if index:
                add(graph_item, "sortorder", str(index))
            add(graph_item, "color", COLORS[index])
            item = add(graph_item, "item")
            add(item, "host", TEMPLATE_NAME)
            add(item, "key", item_key(metric))

    if version == "7.0":
        add_tags(template, "NFS")

    indent_xml(root)
    content = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + content + "\n"


def yaml_metric(metric: Dict[str, Any]) -> Dict[str, Any]:
    item = {
        "uuid": metric["uuid"],
        "name": f'{{#MOUNT_POINT}}: {metric["label"]}',
        "type": "DEPENDENT",
        "key": item_key(metric["key"]),
        "delay": "0",
        "history": "30d",
        "value_type": "FLOAT",
    }
    if metric["unit"]:
        item["units"] = metric["unit"]
    item["description"] = metric["description"]
    preprocessing = {
        "type": "JSONPATH",
        "parameters": [f'$.{metric["key"]}'],
    }
    if metric.get("optional"):
        preprocessing["error_handler"] = "DISCARD_VALUE"
    item["preprocessing"] = [preprocessing]
    item["master_item"] = {"key": MASTER_KEY}
    item["tags"] = [{"tag": "Application", "value": "NFS"}]
    return item


def build_yaml() -> str:
    prototypes = [
        {
            "uuid": MASTER_UUID,
            "name": "{#MOUNT_POINT}: Get NFS client statistics",
            "key": MASTER_KEY,
            "delay": "1m",
            "history": "0",
            "trends": "0",
            "value_type": "TEXT",
            "description": "Raw JSON returned by one nfsiostat sample. Used by dependent item prototypes.",
            "tags": [{"tag": "Application", "value": "NFS raw"}],
        }
    ]
    prototypes.extend(yaml_metric(metric) for metric in METRICS)

    graph_prototypes = []
    for graph in GRAPHS:
        graph_items = []
        for index, metric in enumerate(graph["metrics"]):
            graph_item = {"color": COLORS[index]}
            if index:
                graph_item["sortorder"] = str(index)
            graph_item["item"] = {"host": TEMPLATE_NAME, "key": item_key(metric)}
            graph_items.append(graph_item)
        graph_prototypes.append(
            {
                "uuid": graph["uuid"],
                "name": f'{{#MOUNT_POINT}}: {graph["name"]}',
                "graph_items": graph_items,
            }
        )

    document = {
        "zabbix_export": {
            "version": "7.0",
            "template_groups": [{"uuid": GROUP_UUID, "name": "Templates"}],
            "templates": [
                {
                    "uuid": TEMPLATE_UUID,
                    "template": TEMPLATE_NAME,
                    "name": TEMPLATE_NAME,
                    "description": "NFS client statistics from nfsiostat. Modern templates collect all metrics once per mount and use dependent items.",
                    "vendor": {"name": "CPOS-HPC", "version": "1.5.0"},
                    "groups": [{"name": "Templates"}],
                    "discovery_rules": [
                        {
                            "uuid": DISCOVERY_UUID,
                            "name": "NFS mount point discovery",
                            "key": "nfsio.discovery",
                            "delay": "2m",
                            "lifetime": "1d",
                            "enabled_lifetime_type": "DISABLE_NEVER",
                            "description": "Discovers mounted NFS and NFSv4 filesystems.",
                            "item_prototypes": prototypes,
                            "graph_prototypes": graph_prototypes,
                        }
                    ],
                    "tags": [{"tag": "Application", "value": "NFS"}],
                }
            ],
        }
    }
    class TemplateDumper(yaml.SafeDumper):
        def ignore_aliases(self, data: Any) -> bool:
            return True

    def represent_dict(dumper: TemplateDumper, data: Dict[str, Any]) -> Any:
        return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())

    TemplateDumper.add_representer(dict, represent_dict)
    return yaml.dump(
        document,
        Dumper=TemplateDumper,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    )


OUTPUTS = {
    ROOT / "template_nfsio_zabbix5.xml": lambda: build_xml("5.0"),
    ROOT / "template_nfsio_zabbix7.xml": lambda: build_xml("7.0"),
    ROOT / "template_nfsio_zabbix7.yaml": build_yaml,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if checked-in templates are stale")
    args = parser.parse_args()

    stale = []
    for path, renderer in OUTPUTS.items():
        rendered = renderer()
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != rendered:
                stale.append(path.relative_to(ROOT))
        else:
            path.write_text(rendered, encoding="utf-8")

    if stale:
        print("Generated templates are stale:", file=sys.stderr)
        for path in stale:
            print(f"  {path}", file=sys.stderr)
        return 1

    if not args.check:
        print(f"Generated {len(OUTPUTS)} templates at {dt.datetime.now().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
