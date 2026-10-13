#!/usr/bin/env python3
"""Collect 'show version' output from Cisco IOS-XR, IOS-XE, and NX-OS devices."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from netmiko import ConnectHandler


REQUIRED_COLUMNS = {"Node_IP", "Username", "Password"}
SUPPORTED_DEVICE_TYPES = {
    "cisco_xr": "cisco_xr",
    "ios-xr": "cisco_xr",
    "ios_xr": "cisco_xr",
    "xr": "cisco_xr",
    "cisco_xe": "cisco_xe",
    "ios-xe": "cisco_xe",
    "ios_xe": "cisco_xe",
    "xe": "cisco_xe",
    "cisco_nxos": "cisco_nxos",
    "nx-os": "cisco_nxos",
    "nx_os": "cisco_nxos",
    "nxos": "cisco_nxos",
}


def normalize_device_type(value: str) -> str:
    """Normalize friendly platform names to Netmiko device_type identifiers."""
    normalized = value.strip().lower()
    return SUPPORTED_DEVICE_TYPES.get(normalized, normalized)


def create_template(path: Path, device_type: str) -> None:
    """Create a blank Excel input template and display the intended fallback platform."""
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["Node_IP", "Username", "Password", "Device_Type"]
    pd.DataFrame(columns=columns).to_excel(path, index=False, sheet_name="Nodes")
    print(f"Created blank input template: {path}")
    print(f"Set Device_Type to {normalize_device_type(device_type)} for each node, or use --default-device-type.")


def parse_version(output: str) -> str:
    """Return a best-effort version string for common Cisco platforms."""
    patterns = [
        r"NXOS:\s+version\s+([^\s]+)",
        r"Cisco IOS XE Software, Version\s+([^\s,]+)",
        r"Cisco IOS XR Software, Version\s+([^\s,]+)",
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
    node_ip = str(row.get("Node_IP", "")).strip()
    username = str(row.get("Username", "")).strip()
    password = str(row.get("Password", ""))
    device_type = normalize_device_type(str(row.get("Device_Type", "")).strip() or default_device_type)

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
        description="Collect show version output from Cisco IOS-XR, IOS-XE, and NX-OS nodes listed in Excel or CSV."
    )
    parser.add_argument("--input", help="Input .xlsx or .csv file with Node_IP, Username, Password columns")
    parser.add_argument(
        "--output",
        default=f"prebuild_version_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        help="Output report path (default: timestamped Excel workbook)",
    )
    parser.add_argument(
        "--default-device-type",
        default="cisco_nxos",
        help="Fallback Netmiko type: cisco_xr, cisco_xe, or cisco_nxos (default: cisco_nxos)",
    )
    parser.add_argument("--timeout", type=int, default=15, help="SSH connection/auth timeout in seconds")
    parser.add_argument(
        "--create-template",
        metavar="PATH",
        help="Create a blank Excel input template at PATH and exit",
    )
    args = parser.parse_args()

    if args.create_template:
        create_template(Path(args.create_template), args.default_device_type)
        return 0

    if not args.input:
        parser.error("provide --input FILE.xlsx or FILE.csv, or use --create-template PATH")

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

    default_device_type = normalize_device_type(args.default_device_type)
    if default_device_type not in {"cisco_xr", "cisco_xe", "cisco_nxos"}:
        parser.error("--default-device-type must be cisco_xr, cisco_xe, or cisco_nxos")

    try:
        if input_path.suffix.lower() == ".csv":
            source = pd.read_csv(input_path, dtype=str).fillna("")
        elif input_path.suffix.lower() == ".xlsx":
            source = pd.read_excel(input_path, dtype=str).fillna("")
        else:
            print("Unsupported input format. Use .xlsx or .csv.", file=sys.stderr)
            return 2
    except Exception as exc:
        print(f"Could not read input file (supported formats: .xlsx, .csv): {exc}", file=sys.stderr)
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
        result = collect_one(row, default_device_type, args.timeout)
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
