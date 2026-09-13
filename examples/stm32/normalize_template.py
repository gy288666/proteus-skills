"""Normalize a disposable copy through the public native API."""
from pathlib import Path
import argparse
import hashlib, json, shutil
from proteus_automatic_api import Circuit, Session, Simulation

root = Path(__file__).parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sample', type=Path, default=Path(r'C:\ProgramData\program\SAMPLES\VSM for Cortex M3\STM32\STMCubeMX LED Blink\STMCubeMX LED Blink.pdsprj'))
parser.add_argument('--output', type=Path, default=root / 'STM32-template.pdsprj')
parser.add_argument('--executable', default=r'D:\Proteus\BIN\PDS.EXE')
args = parser.parse_args()
source = args.sample.resolve(strict=True)
target = args.output.resolve()
assert not target.exists()
digest = hashlib.sha256(source.read_bytes()).hexdigest()
shutil.copy2(source, target)
s = Session(target, executable=args.executable)
try:
    Simulation(s).set_firmware('U1', root / 'firmware' / 'hold.hex')
    s.save()
finally:
    s.close()
c = Circuit(template_project=target)
assert c.components() == []
report = {'source': str(source), 'source_unchanged': hashlib.sha256(source.read_bytes()).hexdigest() == digest,
          'source_sha256': digest, 'normalized': str(target), 'blank_components': c.components()}
(root / 'template-normalization.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report), flush=True)
