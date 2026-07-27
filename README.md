# omnipkg-metadata

A curated repository of metadata for the top 500 most popular Python packages. This project automatically collects and maintains compatibility matrices, version histories, and project details from PyPI.

## Features

- **Automated Collection**: Daily updates via GitHub Actions to keep metadata current.
- **Comprehensive Dataset**: Tracks the top 500 Python packages.
- **Detailed Metadata**: For each package, the repository provides:
  - Latest version and full version history.
  - Python version requirements (`requires_python`).
  - Dependency lists (`requires_dist`).
  - Project URLs (Documentation, Source, Issues).
  - Classification tags and licenses.

## Repository Structure

- `index.json`: The main registry mapping package names to their respective metadata files.
- `metadata/*.json`: Individual JSON files containing detailed metadata for each supported package.
- `python-compat/*.json`: Compatibility-specific data for the top 500 packages.
- `scripts/`: Contains the logic used to fetch and process PyPI data.
- `.github/workflows/`: CI/CD pipelines for automated daily updates.

## Usage

### Consuming the Data
You can use this repository as a read-only data source for tools that need to verify Python package compatibility or fetch project metadata without querying the PyPI API in real-time.

1. **Fetch the Index**: Load `index.json` to find the path to a specific package's metadata.
2. **Load Package Data**: Access the JSON file in the `metadata/` or `python-compat/` directory to retrieve versioning and compatibility information.

### Updating Metadata
If you wish to run the metadata collection script locally:

**Installation**
```bash
pip install requests packaging
```

**Execution**
```bash
python scripts/collect_python_compat.py
```

## Automation
The repository is configured with a GitHub Action (`collect-pypi-metadata.yml`) that runs daily at 4 AM UTC to ensure the compatibility matrix remains up to date.
