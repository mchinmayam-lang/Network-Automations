# Pre-Build Node Version Collection

Collect `show version` output over SSH from Cisco **IOS-XR**, **IOS-XE**, and **NX-OS** devices using node details stored in an Excel workbook or CSV file. The script uses Netmiko's platform-specific drivers and writes an Excel report with the detected hostname/version, status, full command output, collection timestamp, and error details.

## Supported Cisco platforms

| Platform | Netmiko `Device_Type` | Template |
| --- | --- | --- |
| Cisco IOS-XR | `cisco_xr` | [templates/ios_xr_nodes.csv](templates/ios_xr_nodes.csv) |
| Cisco IOS-XE | `cisco_xe` | [templates/ios_xe_nodes.csv](templates/ios_xe_nodes.csv) |
| Cisco NX-OS | `cisco_nxos` | [templates/nxos_nodes.csv](templates/nxos_nodes.csv) |

Each template is CSV format, which opens in Microsoft Excel. Each includes example rows with documentation-only IP addresses and placeholder credentials. Replace all example values before running the script. The `192.0.2.0/24` range is reserved for documentation and does not identify real devices.

## Features

- Reads multiple nodes from an `.xlsx` workbook or `.csv` file.
- Uses SSH credentials from the input file.
- Runs the read-only `show version` command on each node.
- Supports mixed IOS-XR, IOS-XE, and NX-OS devices in one input file.
- Selects the Netmiko driver using each row's `Device_Type`; accepts friendly aliases such as `ios-xr`, `ios-xe`, and `nx-os`.
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

## Input file format

Use one of the three platform templates linked above, or create your own input file with one row per device.

| Column | Required | Description | Example |
| --- | --- | --- | --- |
| `Node_IP` | Yes | Management IP or resolvable hostname | `192.0.2.10` |
| `Username` | Yes | SSH username | `automation-user` |
| `Password` | Yes | SSH password | Enter locally in Excel |
| `Device_Type` | Recommended | Netmiko platform identifier | `cisco_xr`, `cisco_xe`, or `cisco_nxos` |

The row's `Device_Type` takes precedence over the fallback `--default-device-type`. For a mixed-platform fleet, set `Device_Type` on every row. If it is blank, the default is `cisco_nxos`.

You can also generate a blank Excel workbook locally:

```bash
# Blank template intended for IOS-XR
python src/collect_versions.py --create-template nodes_ios_xr.xlsx --default-device-type cisco_xr

# Blank template intended for IOS-XE
python src/collect_versions.py --create-template nodes_ios_xe.xlsx --default-device-type cisco_xe

# Blank template intended for NX-OS
python src/collect_versions.py --create-template nodes_nxos.xlsx --default-device-type cisco_nxos
```

The generated workbook contains the required column headers. Set `Device_Type` in each row, or use the matching fallback option when running the script.

## Run the collection

Examples using the platform-specific CSV templates:

```bash
python src/collect_versions.py --input templates/ios_xr_nodes.csv --output reports/ios_xr_version_report.xlsx --default-device-type cisco_xr
python src/collect_versions.py --input templates/ios_xe_nodes.csv --output reports/ios_xe_version_report.xlsx --default-device-type cisco_xe
python src/collect_versions.py --input templates/nxos_nodes.csv --output reports/nxos_version_report.xlsx --default-device-type cisco_nxos
```

To collect from a mixed-platform inventory, put the correct `Device_Type` in each row and use a single input file:

```bash
python src/collect_versions.py --input nodes.xlsx --output reports/prebuild_version_report.xlsx
```

Use `--timeout 25` to change the SSH connection and authentication timeout.

## Report contents

The output workbook contains:

- **Results:** Node IP, detected hostname, device type, detected version (best effort), success/failure status, UTC timestamp, full `show version` output, and error details.
- **Summary:** Total, successful, and failed node counts, plus report generation time.

The script exits with code `0` when all nodes succeed, `1` when one or more nodes fail, and `2` for an input or report-processing error.

## Security and operational notes

- Treat input workbooks as secrets: restrict file permissions and store them in an approved secure location.
- Never commit real credentials, credential-filled workbooks, reports, private keys, or sensitive device output to GitHub.
- Use an approved least-privilege account and test in a lab before wider use.
- The script uses SSH through Netmiko. Validate SSH host-key and trust requirements against your organization's policy before running in a sensitive environment.
- The script only runs `show version`; it does not intentionally change device configuration.
- Error messages may contain device or network details. Review the generated report before sharing it.

## Troubleshooting

- **Timeout / connection refused:** Verify routing, management reachability, SSH service, ACLs, and TCP port 22.
- **Authentication failure:** Verify the username/password and account access policy.
- **Unsupported device type:** Use the Netmiko identifier for the platform and check your installed Netmiko version.
- **Missing columns:** Use a supplied template and keep the required headers exactly as shown.
- **Version shows `See full output`:** The full command output is retained in the report; the parser may need adjustment for an unusual software output format.

## Validation status

The script has been updated for all three Cisco platforms and the templates are based on Netmiko's documented device-type identifiers. It has not been tested against your actual network devices; validate it against at least one lab device per platform before operational use.
