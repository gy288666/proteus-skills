"""Ensure the task can import proteus-automatic-api, installing from GitHub if needed."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import venv


REPOSITORY = "kudoumakoto6523-design/Proteus_automatic_package"
PROBE = """import json
from importlib.metadata import distribution
import proteus_automatic_api as api
from proteus_automatic_api import Circuit, Library, Session, Simulation
dist = distribution('proteus-automatic-api')
assert dist.metadata['Name'] == 'proteus-automatic-api'
print(json.dumps(dict(version=dist.version, module=api.__file__,
                     source=json.loads(dist.read_text('direct_url.json') or 'null'))))
"""


def probe(python):
    result = subprocess.run([str(python), "-I", "-c", PROBE], capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Proteus-Skills-setup"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def ensure(environment=None, update=False):
    if os.name != "nt" or sys.version_info < (3, 10):
        raise RuntimeError("Use Windows and Python 3.10 or newer")
    # Reuse the active task environment or an already usable interpreter.
    if environment is None and (sys.prefix != sys.base_prefix or probe(sys.executable)):
        python = Path(sys.executable)
    else:
        environment = Path(environment or ".venv-proteus").resolve()
        python = environment / "Scripts" / "python.exe"
        if environment.exists():
            if not (environment / "pyvenv.cfg").is_file() or not python.is_file():
                raise RuntimeError(f"Not a usable virtual environment: {environment}")
        else:
            venv.EnvBuilder(with_pip=True).create(environment)
    installed = probe(python)
    if installed and not update:
        return dict(action="reused", python=str(python), **installed)

    api = f"https://api.github.com/repos/{REPOSITORY}"
    repository = json.loads(fetch(api))
    branch = urllib.parse.quote(repository["default_branch"], safe="")
    commit = json.loads(fetch(f"{api}/commits/{branch}"))["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("GitHub returned an invalid commit SHA")
    source = f"https://raw.githubusercontent.com/{REPOSITORY}/{commit}"
    manifest = fetch(f"{source}/pyproject.toml")
    # Check this repository's literal project name before invoking its build backend.
    project = re.search(r"(?ms)^\[project\][ \t]*\r?\n(.*?)(?=^\[|\Z)", manifest)
    if not project or not re.search(
            r"(?m)^name\s*=\s*(['\"])proteus-automatic-api\1\s*$", project[1]):
        raise RuntimeError("The official repository does not declare proteus-automatic-api")
    fetch(f"{source}/api/proteus_automatic_api.py")
    archive = f"https://github.com/{REPOSITORY}/archive/{commit}.zip"
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "--force-reinstall",
                    f"proteus-automatic-api @ {archive}"], check=True, stdout=sys.stderr)
    installed = probe(python)
    if not installed or (installed.get("source") or {}).get("url") != archive:
        raise RuntimeError("Installed library failed its import or source verification")
    return dict(action="installed", python=str(python), commit=commit, **installed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", type=Path, help="Use or create this task virtual environment")
    parser.add_argument("--update", action="store_true", help="Install the latest GitHub commit")
    args = parser.parse_args()
    try:
        print(json.dumps(ensure(args.venv, args.update), ensure_ascii=True))
    except Exception as exc:
        print(f"Environment setup failed: {exc}", file=sys.stderr)
        sys.exit(1)
