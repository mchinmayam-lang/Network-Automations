#!/usr/bin/env python3
"""Collect 'show version' output from network devices listed in an Excel workbook."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from netmiko import ConnectHandler


REQUIRED_COLUMNS = {"Node_IP", "Username", "Password"}
OPTIONAL_COLUMNS = {"Device_Type"}


def create_template(path: Path) -> None:
    """Create an empty Excel input template with the required column names."""
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["Node_IP", "Username", "Password", "Device_Type"]
    pd.DataFrame(columns=columns).to_excel(path, index=False, sheet_name="Nodes")
    print(f"Created input template: {path}")


def parse_version(output: str) -> str:
    """Return a best-effort version string for common Cisco platforms."""
    patterns = [
        r"NXOS:\s+version\s+([^\s]+)",
        r"Cisco IOS XE Software, Version\s+([^\s,]+)",
        r"Cisco IOS Software.*Version\s+([^,\s]+)",
        r"system:\s+version\s+([^\s]+)",
        r"\bVersion\s+([0-9][A-Za-z0-9()._-]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, output, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return "See full output"


def parse_hostname(output: str, prompt: str = "") -> str:
    """Try to find a hostname in command output or the device prompt."""
    patterns = [
        r"(?im)^\s*Device name:\s*(\S+)",
        r"(?im)^\s*hostname\s+(\S+)",
        r"(?im)^\s*switchname\s+(\S+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1).strip()
    cleaned = prompt.strip().rstrip("#>").strip()
    return cleaned or "Unknown"


def collect_one(row: dict[str, str], default_device_type: str, timeout: int) -> dict[str, str]:
    """Connect to one device, run show version, and return a report row."""
    node_ip = row.get("Node_IP", "").strip()
    username = row.get("Username", "").strip()
    password = row.get("Password", "")
    device_type = row.get("Device_Type", "").strip() or default_device_type

    result = {
        "Node_IP": node_ip,
        "Hostname": "",
        "Device_Type": device_type,
        "Version": "",
        "Status": "FAILED",
        "Collected_At_UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "Version_Output": "",
        "Error": "",
    }

    if not node_ip or not username or not password:
        result["Error"] = "Missing Node_IP, Username, or Password in the input row."
        return result

    connection = None
    try:
        connection = ConnectHandler(
            device_type=device_type,
            host=node_ip,
            username=username,
            password=password,
            conn_timeout=timeout,
            auth_timeout=timeout,
            banner_timeout=timeout,
            fast_cli=False,
        )
        output = connection.send_command(
            "show version",
            read_timeout=max(timeout * 2, 30),
            strip_prompt=False,
            strip_command=False,
        )
        result["Hostname"] = parse_hostname(output, connection.find_prompt())
        result["Version"] = parse_version(output)
        result["Version_Output"] = output.strip()
        result["Status"] = "SUCCESS"
    except Exception as exc:
        # Exception messages are recorded, but credentials are never deliberately logged.
        message = " ".join(str(exc).split())
        for secret in (password, username):
            if secret:
                message = message.replace(secret, "[REDACTED]")
        result["Error"] = message[:1000] or exc.__class__.__name__
    finally:
        if connection is not None:
            try:
                connection.disconnect()
            except Exception:
                pass

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect show version output from nodes listed in an Excel workbook."
    )
    parser.add_argument("--input", help="Input .xlsx file with Node_IP, Username, Password columns")
    parser.add_argument(
        "--output",
        default=f"prebuild_version_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        help="Output report path (default: timestamped Excel workbook)",
    )
    parser.add_argument(
        "--default-device-type",
        default="cisco_nxos",
        help="Netmiko device_type used when Device_Type is blank (default: cisco_nxos)",
    )
    parser.add_argument("--timeout", type=int, default=15, help="SSH connection/auth timeout in seconds")
    parser.add_argument(
        "--create-template",
        metavar="PATH",
        help="Create an empty input Excel template at PATH and exit",
    )
    args = parser.parse_args()

    if args.create_template:
        create_template(Path(args.create_template))
        return 0

    if not args.input:
        parser.error("provide --input FILE.xlsx or use --create-template PATH")

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2
    if input_path.resolve() == output_path.resolve():
        print("Input and output paths must be different.", file=sys.stderr)
        return 2
    if args.timeout < 1:
        parser.error("--timeout must be at least 1 second")

    try:
        source = pd.read_excel(input_path, dtype=str).fillna("")
    except Exception as exc:
        print(f"Could not read input workbook: {exc}", file=sys.stderr)
        return 2

    missing = REQUIRED_COLUMNS - set(source.columns)
    if missing:
        print(f"Input workbook is missing required columns: {', '.join(sorted(missing))}", file=sys.stderr)
        print(f"Required columns: {', '.join(sorted(REQUIRED_COLUMNS))}", file=sys.stderr)
        return 2

    rows = source.to_dict(orient="records")
    if not rows:
        print("The input workbook contains no device rows.", file=sys.stderr)
        return 2

    results = []
    total = len(rows)
    for index, row in enumerate(rows, start=1):
        node_ip = str(row.get("Node_IP", "")).strip() or f"row {index}"
        print(f"[{index}/{total}] Collecting version from {node_ip} ...")
        result = collect_one(row, args.default_device_type, args.timeout)
        print(f"  {result['Status']}: {result['Hostname'] or result['Node_IP']}")
        results.append(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            pd.DataFrame(results).to_excel(writer, index=False, sheet_name="Results")
            summary = pd.DataFrame(
                [
                    {"Metric": "Total nodes", "Value": len(results)},
                    {"Metric": "Successful", "Value": sum(r["Status"] == "SUCCESS" for r in results)},
                    {"Metric": "Failed", "Value": sum(r["Status"] == "FAILED" for r in results)},
                    {"Metric": "Generated at UTC", "Value": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                ]
            )
            summary.to_excel(writer, index=False, sheet_name="Summary")
    except Exception as exc:
        print(f"Could not write output workbook: {exc}", file=sys.stderr)
        return 2

    successful = sum(result["Status"] == "SUCCESS" for result in results)
    print(f"\nReport saved to: {output_path}")
    print(f"Completed: {successful}/{total} node(s) succeeded.")
    return 0 if successful == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
