"""Integration check: GitHub installation into an empty environment, then reuse."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile


with tempfile.TemporaryDirectory(prefix="proteus-skill-setup-") as directory:
    task = Path(directory)
    assert task.resolve().parent == Path(tempfile.gettempdir()).resolve()
    script = Path(__file__).with_name("ensure_library.py")
    command = [sys.executable, str(script), "--venv", str(task / ".venv-proteus")]
    first = subprocess.run(command, cwd=task, capture_output=True, text=True, check=True)
    installed = json.loads(first.stdout)
    assert installed["action"] == "installed" and len(installed["commit"]) == 40
    # Continue a real Python task using the interpreter returned by setup.
    continued = subprocess.run([installed["python"], "-I", "-c",
        "from proteus_automatic_api import Circuit, Library, Session, Simulation; "
        "assert all(callable(x) for x in (Circuit, Library, Session, Simulation)); print('task continued')"],
        cwd=task, capture_output=True, text=True, check=True)
    assert continued.stdout.strip() == "task continued"
    second = subprocess.run(command, cwd=task, capture_output=True, text=True, check=True)
    reused = json.loads(second.stdout)
    assert reused["action"] == "reused" and reused["python"] == installed["python"]
    assert reused["source"] == installed["source"]
    print(json.dumps(dict(fresh_install=True, continued_task=True, reused=True,
                         commit=installed["commit"], version=installed["version"])))
