import json
import requests
import sys
import time
from pathlib import Path
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

# Configuration
PYTHON_VERSIONS = ["3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
TOP_N = 500
MAX_RETRIES = 3

def get_latest_compatible(pkg_name, releases_data):
    compat_map = {py: None for py in PYTHON_VERSIONS}
    sorted_versions = []
    
    for ver_str in releases_data:
        try:
            v = Version(ver_str)
            if not v.is_prerelease:
                sorted_versions.append(v)
        except InvalidVersion:
            continue
            
    sorted_versions.sort(reverse=True)

    for py_ver in PYTHON_VERSIONS:
        found = False
        for ver in sorted_versions:
            ver_str = str(ver)
            release_info = releases_data[ver_str]
            requires_python = None
            upload_time = None
            
            if isinstance(release_info, list) and release_info:
                requires_python = release_info[0].get('requires_python')
                upload_time = release_info[0].get('upload_time')

            if requires_python is None:
                compat_map[py_ver] = {"version": ver_str, "released": upload_time}
                found = True
                break

            try:
                spec = SpecifierSet(requires_python)
                if spec.contains(f"{py_ver}.0"):
                    compat_map[py_ver] = {"version": ver_str, "released": upload_time}
                    found = True
                    break
            except Exception:
                continue
        
        if not found:
             compat_map[py_ver] = None

    return compat_map

def fetch_pypi_json(pkg_name):
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(f"https://pypi.org/pypi/{pkg_name}/json", timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                print(f"  ❌ {pkg_name} not found on PyPI")
                return None
        except requests.RequestException as e:
            print(f"  ⚠️ Attempt {attempt+1}/{MAX_RETRIES} failed for {pkg_name}: {e}")
            time.sleep(1)
    return None

def main():
    print(f"📥 Fetching Top {TOP_N} PyPI packages...")
    try:
        r = requests.get("https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json", timeout=30)
        top_packages = [p["project"] for p in r.json()["rows"][:TOP_N]]
    except Exception as e:
        print(f"❌ Failed to fetch top packages list: {e}")
        sys.exit(1)

    out_dir = Path("python-compat")
    out_dir.mkdir(exist_ok=True)
    
    index = {}
    success_count = 0
    
    print(f"🚀 Analyzing {len(top_packages)} packages...")

    for i, pkg in enumerate(top_packages, 1):
        try:
            if i % 10 == 0:
                print(f"[{i}/{TOP_N}] Processing {pkg}...")
            
            data = fetch_pypi_json(pkg)
            if not data:
                continue
                
            releases = data.get("releases", {})
            compat_matrix = get_latest_compatible(pkg, releases)
            
            result = {
                "package": pkg,
                "last_updated": data["info"].get("version"),
                "python_compatibility": compat_matrix
            }
            
            with open(out_dir / f"{pkg}.json", "w") as f:
                json.dump(result, f, indent=2)
            
            index[pkg] = f"python-compat/{pkg}.json"
            success_count += 1

        except Exception as e:
            print(f"  🔥 CRITICAL ERROR skipping {pkg}: {e}")
            continue

    with open("index.json", "w") as f:
        json.dump({"updated": "now", "packages": index, "total_processed": success_count}, f, indent=2)
    
    print(f"✅ Scan Complete. Processed {success_count}/{TOP_N} packages.")

if __name__ == "__main__":
    main()
