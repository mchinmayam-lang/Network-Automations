# Pre-Build Node Version Collection

Collect the output of `show version` from network devices over SSH using node details stored in an Excel workbook. The automation writes an Excel report with the device status, detected hostname/version, full command output, collection timestamp, and any error message.

## Features

- Reads multiple nodes from an `.xlsx` input workbook.
- Uses SSH credentials from the input file.
- Runs `show version` on each node.
- Supports per-node Netmiko `Device_Type`, with Cisco NX-OS as the default.
- Continues to the next node if a connection or command fails.
- Writes a report with `Results` and `Summary` worksheets.
- Does not intentionally print or write passwords into the report.

## Requirements

- Python 3.10 or later recommended.
- SSH reachability from the computer running the script.
- A valid account on each target device with permission to run `show version`.
- Device access approved by the network owner.

## Setup

From this project directory, create a virtual environment and install dependencies.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 1. Create the input Excel template

```bash
python src/collect_versions.py --create-template nodes.xlsx
```

Fill in the generated workbook with one row per device. Do not commit this workbook to GitHub because it contains credentials.

| Column | Required | Description | Example |
| --- | --- | --- | --- |
| `Node_IP` | Yes | Management IP or resolvable hostname | `192.0.2.10` |
| `Username` | Yes | SSH username | `automation-user` |
| `Password` | Yes | SSH password | Enter locally in Excel |
| `Device_Type` | No | Netmiko platform identifier | `cisco_nxos` |

The example IP above is a documentation-only address. Replace it with an authorized lab or production target. The `Device_Type` column can be left blank to use the default.

Common Netmiko identifiers include `cisco_nxos` for Cisco Nexus NX-OS, `cisco_ios` for Cisco IOS, and `cisco_xe` for Cisco IOS XE. Confirm the correct identifier for your device and installed Netmiko version.

## 2. Run the collection

For Cisco Nexus / NX-OS devices:

```bash
python src/collect_versions.py --input nodes.xlsx --output reports/prebuild_version_report.xlsx
```

For a different default platform:

```bash
python src/collect_versions.py --input nodes.xlsx --output reports/prebuild_version_report.xlsx --default-device-type cisco_ios
```

A per-row `Device_Type` value takes precedence over the default. Use `--timeout 25` to change the SSH connection and authentication timeout.

## 3. Review the report

The output workbook contains:

- **Results:** Node IP, detected hostname, device type, detected version (best effort), success/failure status, UTC timestamp, full `show version` output, and error details.
- **Summary:** Total, successful, and failed node counts, plus report generation time.

The script exits with code `0` when all nodes succeed, `1` when one or more nodes fail, and `2` for an input or report-processing error.

## Security and operational notes

- Treat the input workbook as a secret: restrict file permissions, store it in an approved secure location, and delete it securely when no longer needed.
- Never commit real credentials, credential-filled workbooks, reports, private keys, or sensitive device output to GitHub.
- Use an approved least-privilege account and test in a lab before wider use.
- The script uses SSH host connections through Netmiko. Before running in a sensitive environment, validate host-key and SSH trust requirements against your organization's policy.
- The script only runs `show version`; it does not intentionally change device configuration.
- Error messages may contain device or network details. Review the generated report before sharing it.

## Troubleshooting

- **Timeout / connection refused:** Verify routing, management reachability, SSH service, ACLs, and TCP port 22.
- **Authentication failure:** Verify the username/password and account access policy.
- **Unsupported device type:** Check the Netmiko platform identifier and installed version.
- **Missing columns:** Use the generated template and keep the required headers exactly as shown.
- **Version shows `See full output`:** The full command output is retained in the report; adjust the parser for that platform's output format if needed.

## Validation status

This initial implementation has been reviewed for structure and error-handling logic, but it has not been tested against your actual network devices. Validate it against a lab node and confirm the report output before operational use.
