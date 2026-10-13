# Network Automation

A growing collection of practical network automation projects, with an initial focus on making network operations more consistent, repeatable, and easier to maintain.

> **Project status:** Work in progress. This repository is a home for multiple automation projects. Individual tools, supported platforms, and usage instructions will be documented as they are added.

## Goals

- Reduce repetitive manual network tasks.
- Improve configuration consistency and operational reliability.
- Make automation workflows easier to review, test, and reuse.
- Document prerequisites, execution steps, and rollback considerations for each project.
- Build a foundation for automating network platforms such as Cisco ACI and Cisco Nexus / NX-OS.

## Repository layout

The repository currently starts with this README. As projects are added, a suggested structure is:

```text
Network-Automations/
├── README.md
├── projects/
│   ├── aci/
│   │   └── README.md
│   └── nxos/
│       └── README.md
├── shared/
│   └── README.md
├── tests/
├── docs/
└── .gitignore
```

This is a proposed layout, not a claim that these directories or automation scripts already exist.

## Getting started

### 1. Prerequisites

For the repository itself, you need:

- Git
- Access to this GitHub repository
- A terminal or command prompt

Each automation project may require additional software, Python packages, API access, device connectivity, or platform-specific tools. Check that project's README before running it.

### 2. Clone the repository

Because this repository is private, make sure you have authenticated with GitHub and have permission to access it.

```bash
git clone https://github.com/mchinmayam-lang/Network-Automations.git
cd Network-Automations
```

### 3. Review the available projects

Start with this README and then open the README inside the relevant project directory once a project has been added. Do not assume a script is ready for production merely because it is present in the repository.

## Planned project areas

These are possible areas of development; they are not yet implemented by this README update.

| Area | Potential capabilities |
| --- | --- |
| Cisco ACI | Inventory and fabric data collection, health checks, and controlled policy workflows |
| Cisco Nexus / NX-OS | Configuration generation, pre-checks, state collection, and configuration validation |
| Shared utilities | Input validation, logging, reusable connection helpers, and common reporting |
| Testing and documentation | Lab test cases, example inputs, expected results, and operational runbooks |

The actual scope and supported versions will be documented for each project as it is implemented.

## Safe usage guidelines

Network automation can affect production services. Before running any automation:

1. Read the project-specific documentation and inspect the code.
2. Test in a lab or non-production environment first.
3. Confirm target devices, credentials, and input files.
4. Use least-privilege accounts and keep secrets out of source control.
5. Review proposed changes and capture the current configuration or state where appropriate.
6. Define a rollback or recovery plan before making changes.
7. Never run an unreviewed script against production infrastructure.

Prefer environment variables or an approved secrets manager for credentials. Do not commit passwords, API tokens, private keys, device configuration backups containing secrets, or other sensitive data.

## Development conventions

As projects are introduced, aim to include:

- A dedicated project README with purpose, prerequisites, setup, examples, and limitations.
- Dependency declarations such as `requirements.txt` or `pyproject.toml` when Python is used.
- Example input files with sensitive values removed.
- Safe defaults, input validation, clear logging, and useful error messages.
- Tests or lab validation steps before operational use.
- A note describing whether a workflow is read-only or changes device state.

## Contributing

1. Create a feature branch for your change.
2. Keep each change focused and document new behavior.
3. Test changes in a suitable lab environment.
4. Review the diff to ensure no secrets or sensitive information are included.
5. Submit a pull request or review the change before merging it into the default branch.

## License

No license has been specified yet. Unless and until a license is added, do not assume that this repository grants permission to reuse or redistribute its contents.
