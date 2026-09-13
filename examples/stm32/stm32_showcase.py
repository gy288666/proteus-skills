"""Build each STM32 demo from blank, optionally recording every public API step."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))
from proteus_automatic_api import Circuit, Project, Library, Session, Simulation, gpio_events
from observe import capture
from record import Recorder

ROOT = Path(__file__).parent
TEMPLATE = ROOT / 'STM32-template.pdsprj'
TITLES = {'hold': 'STM32 / Hold button to light LED',
          'toggle': 'STM32 / Press once to toggle LED',
          'dual': 'STM32 / Two buttons, two independent LEDs'}


def construction(scene):
    """Each tuple is an actual public method invocation, in execution order."""
    yield 'Place STM32F103R6', 'add', ('STM32F103R6', 'U1', 'STM32F103R6', 1524000, 4572000), {}
    for channel in range(1, 3 if scene == 'dual' else 2):
        y = 4318000 if channel == 1 else 2540000
        ref = f'SW{channel}'
        yield f'Place button {ref}', 'add', ('BUTTON', ref, 'BUTTON', -6096000, y), {'properties': {'STATE': '0'}}
        yield f'Position {ref} labels', 'update', (ref,), {'label_offsets': {
            'reference': (-508000, 762000), 'value': (1016000, 508000),
            'device': (1016000, 254000), 'properties': (1016000, -254000)}}
        ry, dy = (1270000, 0) if channel == 1 else (-2032000, -3302000)
        yield f'Place current-limiting resistor R{channel}', 'add', ('RES', f'R{channel}', '470', -2540000, ry), {'rotation': 90}
        yield f'Position R{channel} labels', 'update', (f'R{channel}',), {'label_offsets': {
            'reference': (-508000, 1016000), 'value': (-508000, 635000)}}
        yield f'Place output LED D{channel}', 'add', ('LED-YELLOW', f'D{channel}', 'LED-YELLOW', -6096000, dy), {}
    yield 'Configure 3.3 V supplies and hidden power pins', 'configure_power', (
        {'GND': 0, 'VCC/VDD': 3.3, 'VEE': -3.3},
        {'VCC': 'VCC/VDD', 'VDD': 'VCC/VDD', 'VDDA': 'VCC/VDD', 'VSS': 'GND', 'VSSA': 'GND'}), {}
    yield 'Read the actual MCU pins', 'pins', ('U1',), {}
    yield 'Wire button 1 to PA0', 'connect', ('SW1.2', 'U1.PA0-WKUP'), {}
    if scene == 'dual':
        yield 'Wire button 2 to PA1', 'connect', ('U1.PA1', 'SW2.2'), {}
    for channel in range(1, 3 if scene == 'dual' else 2):
        py, ry, lane = (3048000, 1270000, 0) if channel == 1 else (2794000, -2032000, 508000)
        yield f'Wire PA{channel + 4} through R{channel}', 'connect', (f'U1.PA{channel + 4}', f'R{channel}.2'), {'points': [(1016000, py), (lane, py), (lane, ry), (-1778000, ry)]}
        yield f'Wire R{channel} to LED anode', 'connect', (f'R{channel}.1', f'D{channel}.A'), {}
        yield f'Ground LED {channel} cathode', 'add_terminal', ('ground', '', f'D{channel}.K'), {}
        yield f'Power button {channel}', 'add_terminal', ('power', 'VCC', f'SW{channel}.1'), {}
    for pin in ('VDD', 'VBAT', 'VREF+', 'NRST'):
        yield f'Connect MCU {pin} to 3.3 V', 'add_terminal', ('power', 'VCC', 'U1.' + pin), ({'position': (3048000, 5207000)} if pin == 'VDD' else {})
    for pin in ('VSS', 'BOOT0'):
        yield f'Ground MCU {pin}', 'add_terminal', ('ground', '', 'U1.' + pin), ({'position': (3048000, -4699000)} if pin == 'VSS' else {})
    yield 'Bind native button controls', 'bind_controls', (('SW1', 'SW2') if scene == 'dual' else ('SW1',)), {}


def check_nets(data, scene):
    nets = [{(p['ref'], p['pin']) for p in net['pins']} for net in data['nets']]
    def same(*pins):
        assert any(set(pins) <= net for net in nets), pins
    for channel in range(1, 3 if scene == 'dual' else 2):
        same((f'SW{channel}', '2'), ('U1', 'PA0-WKUP' if channel == 1 else 'PA1'))
        same(('U1', f'PA{channel + 4}'), (f'R{channel}', '2'))
        same((f'R{channel}', '1'), (f'D{channel}', 'A'))
        ground = next(n for n in data['nets'] if n['name'] == 'GND')
        assert (f'D{channel}', 'K') in {(p['ref'], p['pin']) for p in ground['pins']}
    assert len(data['parts']) == (7 if scene == 'dual' else 4)
    assert all(data['parts'][ref]['value'] == '330' for ref in data['parts'] if ref.startswith('R'))


def run(scene, out, record=False, template=TEMPLATE, executable=r'D:\Proteus\BIN\PDS.EXE'):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    firmware = ROOT / 'firmware' / (scene + '.hex')
    template = Path(template).resolve(strict=True)
    sources = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (template, firmware)}
    rec = Recorder(out / 'recording', TITLES[scene]).start() if record else None
    s = sim = None
    rows = []
    report = {'scene': scene, 'passed': False, 'api_calls': rows, 'sources': sources}
    project = out / ('STM32-' + scene + '.pdsprj')

    def event(stage, call, result='', dwell=0):
        row = {'stage': stage, 'call': call, 'result': result, 'time': time.time()}
        rows.append(row)
        print(stage + ' | ' + call, flush=True)
        if rec:
            rec.set_event(stage, call, result, pid=s.pid if s else None, prefix=project.stem)
        if dwell:
            time.sleep(dwell)

    def close():
        nonlocal s, sim
        if s:
            event('Close the displayed stage', 's.close()')
            code = s.close()
            assert code == 0
            s = sim = None

    def display():
        nonlocal s
        event('Open the saved stage in Proteus', 's = Session(project)')
        s = Session(project, executable=executable)
        event('Fit the native schematic view', 's.menu("View/Zoom To View Entire Sheet"); s.menu("View/Zoom In")')
        s.menu('View/Zoom To View Entire Sheet')
        time.sleep(.15)
        s.menu('View/Zoom In')
        time.sleep(.8)

    try:
        event('Create an empty schematic', 'c = Circuit(template_project=template_path)')
        c = Circuit(template_project=template)
        assert c.components() == [] and c.connections() == []
        c.save(project, title=TITLES[scene])
        display()
        event('Empty project: no placed components or wires', 'c.components(); c.connections()', '[]; []', 2 if record else .2)
        library = Library()
        for device, lib in [('STM32F103R6', 'CM3_STM32'), ('BUTTON', 'ACTIVE'), ('RES', 'DEVICE'), ('LED-YELLOW', 'ACTIVE')]:
            limit = 500 if device == 'RES' else 5
            query = f'library.search({device!r}, limit={limit})'
            event('Find ' + device, query)
            found = library.search(device, limit=limit)
            assert any(r['name'] == device for r in found), found
            event('Exact matches for ' + device, query, [{'name':r['name'], 'library':r['library']} for r in found if r['name'] == device], 1.2 if record else 0)
            query = f'library.get({device!r}, library={lib!r})'
            event('Select ' + device, query)
            selected = library.get(device, library=lib)
            assert selected['name'] == device
            event('Selected ' + device, query, {'name': selected['name'], 'library': selected['library'], 'template_definition': 'Reuse existing prototype where available'}, 1.2 if record else 0)
        close()
        event('Import the button definition', 'c.import_device("BUTTON")')
        c.import_device('BUTTON')
        for title, method, args, kwargs in construction(scene):
            call = 'c.' + method + '(' + ', '.join([*(repr(a) for a in args), *(k + '=' + repr(v) for k, v in kwargs.items())]) + ')'
            event(title, call)
            result = getattr(c, method)(*args, **kwargs)
            if method == 'pins':
                event(title, call, [p for p in result if p['name'] in ('PA0-WKUP', 'PA1', 'PA5', 'PA6')], 1 if record else 0)
                continue
            # A newly added part's label adjustment belongs to the same placement.
            # The continuous API log still records each public call independently.
            if method == 'add' and args[0] in ('BUTTON', 'RES'):
                continue
            event('Save the current construction step', 'c.save(project, overwrite=True)')
            c.save(project, overwrite=True)
            if record:
                display()
                event(title, call, 'Saved stage displayed in the native application', 2.5)
                close()
        c.save(project, overwrite=True)
        display()
        capture(pid=s.pid)[0].save(out / 'layout.png')
        sim = Simulation(s)
        event('Load the compiled application firmware', f'sim.set_firmware("U1", "{firmware.name}")')
        report['firmware'] = sim.set_firmware('U1', firmware)
        event('Enable GPIO trace', 's.set_properties("U1", TRACE_GPIO="3")')
        s.set_properties('U1', TRACE_GPIO='3')
        for channel in range(1, 3 if scene == 'dual' else 2):
            event('Set the LED current-limiting resistor', f's.set_properties("R{channel}", VALUE="330")')
            s.set_properties(f'R{channel}', VALUE='330')
            event('330 ohm resistor configured', f's.set_properties("R{channel}", VALUE="330")', 'Native ADI readback confirmed', 1.5 if record else 0)
        event('Save the configured project', 's.save()')
        s.save()
        close()
        reopened = Project(project)
        assert all(p['value'] == '330' for p in reopened.components() if p['ref'].startswith('R'))
        display()
        sim = Simulation(s)
        event('Verify native parts and connectivity', 's.export_netlist("circuit.sdf")')
        sdf = s.export_netlist(out / 'circuit.sdf')
        check_nets(sdf, scene)
        report['netlist_verified'] = True
        event('Native netlist checks passed', 'check_nets(sdf, scene)', f'{len(sdf["parts"])} parts; inputs, outputs and grounds verified', 2 if record else 0)
        actions = [('initial', None, [0, 0] if scene == 'dual' else [0])]
        if scene == 'hold':
            actions += [('press', 'SW1', [1]), ('release', 'SW1', [0]), ('press', 'SW1', [1]), ('release', 'SW1', [0])]
        elif scene == 'toggle':
            actions += [('press', 'SW1', [1]), ('held', None, [1]), ('release', 'SW1', [1]), ('press', 'SW1', [0]), ('release', 'SW1', [0])]
        else:
            actions += [('press', 'SW1', [1, 0]), ('press', 'SW2', [1, 1]), ('release', 'SW1', [0, 1]), ('release', 'SW2', [0, 0])]
        report['simulation'] = []
        for index, (action, ref, expected) in enumerate(actions):
            if ref:
                event('Operate ' + ref, f'sim.{action}("{ref}")')
                command = getattr(sim, action)(ref)
                assert sim.control_state(ref) == (1 if action == 'press' else 0)
            else:
                command = None
            event('Run the MCU firmware', 'sim.run_for(0.01)')
            result = sim.run_for(.01)
            time.sleep(.5)
            capture(pid=s.pid)[0].save(out / f'state-{index}.png')
            event('Read the actual MCU GPIO trace', 'log = sim.log(); gpio_events(log, ref="U1", port=0)')
            log = sim.log()
            (out / 'simulation.log').write_text(log, encoding='utf-8')
            events = [gpio_events(log, ref='U1', port=0, pin=pin) for pin in range(5, 5 + len(expected))]
            levels = [items[-1]['value'] if items else None for items in events]
            assert levels == expected, (action, levels, expected)
            previous = report['simulation'][-1]['levels'] if report['simulation'] else None
            if command:
                for channel, items in enumerate(events):
                    if previous[channel] != expected[channel]:
                        assert command['command_time_seconds'] < items[-1]['seconds'] <= result['end_seconds']
            report['simulation'].append(dict(action=action, ref=ref, command=command, run=result, levels=levels, events=events))
            event(f'{action.upper()} / ' + '  '.join(f'PA{p + 5}={v}' for p, v in enumerate(levels)), 'GPIO trace and button state assertions passed', 'LED state is rendered by Proteus', 5 if record else .2)
            capture(pid=s.pid)[0].save(out / f'verified-{index}.png')
        event('Stop simulation and save the final project', 'sim.stop(); s.save()')
        sim.stop()
        s.save()
        sim = None
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in sources.items())
        report['passed'] = report['sources_unchanged'] = True
        event('PASS / project, netlist and firmware response verified', 'assert report["passed"]', 'Template and firmware unchanged', 3 if record else 0)
        capture(pid=s.pid)[0].save(out / 'final.png')
    finally:
        if rec:
            rec.stop()
            rec = None
        if s and s.process.poll() is None:
            try:
                if sim:
                    sim.stop()
                close()
            except Exception as error:
                report['cleanup_error'] = str(error)
                if s and s.process.poll() is None:
                    s.process.terminate()
                    s.process.wait(timeout=5)
        (out / 'result.json').write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scene', choices=TITLES)
    ap.add_argument('output', type=Path)
    ap.add_argument('--record', action='store_true')
    ap.add_argument('--template', type=Path, default=TEMPLATE)
    ap.add_argument('--executable', default=r'D:\Proteus\BIN\PDS.EXE')
    opts = ap.parse_args()
    run(opts.scene, opts.output, opts.record, opts.template, opts.executable)
