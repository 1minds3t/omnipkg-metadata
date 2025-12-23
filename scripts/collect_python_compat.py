# scripts/collect_python_compat.py
"""
Enhanced PyPI metadata collector with Python version compatibility tracking.
This powers the omnipatcher system by identifying the last supported version
for each Python release.
"""

import json
import requests
from datetime import datetime, timezone
from pathlib import Path
import time
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

def parse_python_requires(requires_python):
    """Parse requires_python string to extract min/max Python versions."""
    if not requires_python:
        return None, None
    
    try:
        spec = SpecifierSet(requires_python)
        # Find minimum version
        min_version = None
        max_version = None
        
        for specifier in spec:
            version_str = str(specifier.version)
            if specifier.operator in ('>=', '>', '~='):
                if not min_version or Version(version_str) < Version(min_version):
                    min_version = version_str
            elif specifier.operator in ('<=', '<'):
                if not max_version or Version(version_str) > Version(max_version):
                    max_version = version_str
        
        return min_version, max_version
    except:
        return None, None

def get_python_compatibility_matrix(package_name):
    """
    Build a matrix of: Python version -> Last supported package version
    
    Example return:
    {
        "3.7": {"version": "3.12.2", "released": "2023-05-20"},
        "3.8": {"version": "3.13.1", "released": "2024-01-15"},
        "3.9": {"version": "3.14.0", "released": "2024-06-10"},
        ...
    }
    """
    resp = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    
    # Python versions to track (3.7 through 3.14)
    python_versions = ["3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
    compat_matrix = {pv: None for pv in python_versions}
    
    # Sort releases by version (newest first)
    try:
        sorted_releases = sorted(
            data["releases"].items(),
            key=lambda x: Version(x[0]),
            reverse=True
        )
    except InvalidVersion:
        # Some packages have weird version strings, fall back to string sort
        sorted_releases = sorted(data["releases"].items(), reverse=True)
    
    # For each release, check which Python versions it supports
    for version, release_files in sorted_releases:
        if not release_files:  # Skip yanked/empty releases
            continue
        
        # Get the upload date from first file
        upload_date = release_files[0].get("upload_time_iso_8601", "")
        
        # Try to get requires_python from any wheel/sdist in this release
        requires_python = None
        for file_info in release_files:
            if file_info.get("requires_python"):
                requires_python = file_info["requires_python"]
                break
        
        if not requires_python:
            # If not in file info, try fetching the specific version metadata
            try:
                ver_resp = requests.get(f"https://pypi.org/pypi/{package_name}/{version}/json", timeout=5)
                ver_data = ver_resp.json()
                requires_python = ver_data["info"].get("requires_python")
            except:
                pass
        
        min_py, max_py = parse_python_requires(requires_python)
        
        # Determine which Python versions this release supports
        for py_ver in python_versions:
            if compat_matrix[py_ver] is not None:
                continue  # Already found a newer version for this Python
            
            # Check if this release supports this Python version
            supports = False
            if not requires_python:
                # No restriction = supports all (assume 3.7+)
                supports = True
            else:
                try:
                    spec = SpecifierSet(requires_python)
                    # Check if py_ver satisfies the spec
                    supports = Version(py_ver + ".0") in spec
                except:
                    supports = False
            
            if supports:
                compat_matrix[py_ver] = {
                    "version": version,
                    "released": upload_date,
                    "requires_python": requires_python
                }
    
    return compat_matrix

# Main collection
TOP_PACKAGES = [
    "filelock", "requests", "numpy", "pandas", "torch", "tensorflow",
    "django", "flask", "fastapi", "pydantic", "pytest", "click",
    "cryptography", "sqlalchemy", "aiohttp", "httpx", "pillow",
    "scipy", "scikit-learn", "matplotlib", "black", "mypy", "setuptools"
]

metadata_dir = Path("metadata")
compat_dir = Path("python-compat")
compat_dir.mkdir(exist_ok=True)

for package in TOP_PACKAGES:
    try:
        print(f"\n{'='*60}")
        print(f"Processing: {package}")
        print('='*60)
        
        # Get compatibility matrix
        compat = get_python_compatibility_matrix(package)
        
        # Save compatibility data
        compat_file = compat_dir / f"{package}.json"
        compat_data = {
            "package": package,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "python_compatibility": compat
        }
        
        with open(compat_file, "w") as f:
            json.dump(compat_data, f, indent=2)
        
        # Print summary
        print(f"\nPython Compatibility Summary for {package}:")
        for py_ver, info in compat.items():
            if info:
                print(f"  Python {py_ver}: {info['version']} (released {info['released'][:10]})")
            else:
                print(f"  Python {py_ver}: Not supported")
        
        time.sleep(0.2)  # Rate limiting
        
    except Exception as e:
        print(f"✗ Failed to process {package}: {e}")
        continue

print("\n✅ Python compatibility matrix collection complete!")
