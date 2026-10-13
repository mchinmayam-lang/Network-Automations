# Network Automation

A growing collection of practical network automation projects, with an initial focus on making network operations more consistent, repeatable, and easier to maintain.

> **Project status:** Work in progress. Each project's documentation describes its current capabilities, prerequisites, and validation status.

## Projects

| Project | Description | Status |
| --- | --- | --- |
| [Cisco Version Collector](projects/cisco-version-collector/README.md) | Connect to nodes over SSH, run `show version`, and export an Excel report. | Initial implementation; validate in a lab before operational use |

## Repository layout

```text
Network-Automations/
├── README.md
└── projects/
    └── cisco-version-collector/
        ├── README.md
        ├── requirements.txt
        ├── .gitignore
        ├── sample_nodes.csv
        ├── templates/
        │   ├── ios_xr_nodes.csv
        │   ├── ios_xe_nodes.csv
        │   └── nxos_nodes.csv
        └── src/
            └── collect_versions.py
```

## Getting started

Clone the repository:

```bash
git clone https://github.com/mchinmayam-lang/Network-Automations.git
cd Network-Automations
```

Then follow the README inside the project you want to run. Individual projects may require Python packages, device access, API credentials, or platform-specific tooling.

## Safe usage guidelines

- Review code and project-specific instructions before running it.
- Test against a lab or non-production device first.
- Use authorized, least-privilege accounts.
- Never commit passwords, API tokens, private keys, credential-filled spreadsheets, or sensitive device output.
- Review generated reports before sharing them.
- Define a rollback plan before using any future automation that changes device state.

## Development conventions

Each project should include its purpose, prerequisites, setup instructions, example usage, limitations, and validation status. Keep automation modular, handle errors clearly, and add tests or lab validation steps as projects mature.

## License

No license has been specified yet. Unless and until a license is added, do not assume that this repository grants permission to reuse or redistribute its contents.
