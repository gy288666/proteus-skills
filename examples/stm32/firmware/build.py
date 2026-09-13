"""Build the three standalone examples with GNU Arm tools already on PATH."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess


root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_build", root / "check_build.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
tools = {name: shutil.which("arm-none-eabi-" + name) for name in ("gcc", "objcopy", "objdump", "size")}
assert all(tools.values()), "Put GNU Arm Embedded tools on PATH"


def run(arguments):
    result = subprocess.run(arguments, cwd=root, capture_output=True, text=True, check=True)
    if result.stderr:
        print(result.stderr, end="")
    return result.stdout


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = {"compiler": run([tools["gcc"], "--version"]).splitlines()[0],
          "linker_sha256": sha(root / "stm32f103_minimal.ld"), "firmware": {}}
flags = ["-mcpu=cortex-m3", "-mthumb", "-O2", "-g", "-ffreestanding", "-fno-builtin",
         "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-Wall", "-Wextra", "-Werror",
         "-nostdlib", "-Wl,--build-id=none", "-T", "stm32f103_minimal.ld"]
for name in ("hold", "toggle", "dual"):
    command = [tools["gcc"], *flags, f"-Wl,-Map={name}.map", f"{name}.c", "-o", f"{name}.elf"]
    run(command)
    run([tools["objcopy"], "-O", "ihex", f"{name}.elf", f"{name}.hex"])
    (root / f"{name}.disassembly.txt").write_text(
        run([tools["objdump"], "-d", "-s", "-j", ".isr_vector", "-j", ".text", f"{name}.elf"]), encoding="utf-8")
    checked = checks.check(root / name)
    checked.update(command=command, source_sha256=sha(root / f"{name}.c"),
                   elf_sha256=sha(root / f"{name}.elf"), hex_sha256=sha(root / f"{name}.hex"),
                   size_output=run([tools["size"], f"{name}.elf"]).strip())
    report["firmware"][name] = checked
(root / "build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
