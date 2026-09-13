"""Passive 6 FPS capture and a native-only 6x GIF encoder without waiting cards.

No application input is sent. Each matching native window is saved uncropped;
an absent target becomes an explicit waiting card, never a desktop screenshot.

  py -3.12 -I record.py encode RECORDING_DIRECTORY DESTINATION.gif
  py -3.12 -I record.py selfcheck NEW_TEST_DIRECTORY
"""
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import threading
import time

from PIL import Image, ImageDraw, ImageFont, ImageOps

_spec = importlib.util.spec_from_file_location("showcase_observe", Path(__file__).with_name("observe.py"))
_observe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_observe)
FPS, SPEED = 6, 6


@lru_cache(maxsize=32)
def _font(size):
    return ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", size)


def _lines(text, font, width):
    lines, line = [], ""
    for char in str(text).replace("\r", ""):
        if char == "\n" or (line and font.getlength(line + char) > width):
            lines.append(line)
            line = "" if char == "\n" else char
        else:
            line += char
    return lines + [line]


def _text(draw, text, box, size, color, max_lines=2):
    left, top, right, bottom = box
    for actual_size in range(size, 10, -1):
        font = _font(actual_size)
        lines = _lines(text, font, right - left)
        if len(lines) <= max_lines and len(lines) * (actual_size + 7) <= bottom - top:
            break
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while font.getlength(lines[-1] + "…") > right - left:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"  # Complete, unabridged strings remain in frame metadata.
    for line in lines:
        draw.text((left, top), line, font=font, fill=color)
        top += actual_size + 7


@lru_cache(maxsize=8)
def _shell(title, stage, call, result, waiting):
    frame = Image.new("RGB", (1280, 900), "#0e1623")
    draw = ImageDraw.Draw(frame)
    _text(draw, title, (24, 15, 1256, 60), 29, "#f1f5fb", 1)
    _text(draw, "API  " + call, (24, 65, 1256, 121), 20, "#74d9ec")
    _text(draw, "RESULT  " + result, (24, 123, 1256, 181), 19, "#c5d0de")
    draw.rounded_rectangle((18, 189, 1262, 816), radius=10, fill="#182332", outline="#42516a", width=2)
    if waiting:
        _text(draw, "Waiting for the matching Proteus window", (90, 440, 1190, 492), 26, "#becbda", 1)
        _text(draw, "The recording continues during file operations and Session startup / close.",
              (90, 499, 1190, 570), 19, "#8192aa")
    _text(draw, stage, (24, 829, 1256, 860), 21, "#f1f5fb", 1)
    _text(draw, "FILE API + NATIVE SESSION  /  PASSIVE RECORDING", (24, 867, 1256, 895), 15, "#8192aa", 1)
    return frame


def _display(title, native, event):
    frame = _shell(title, event["stage"], event["call"], event["result"], native is None).copy()
    if native is not None:
        fitted = ImageOps.contain(native.convert("RGB"), (1232, 615), Image.Resampling.LANCZOS)
        frame.paste(fitted, (24 + (1232 - fitted.width) // 2, 195 + (615 - fitted.height) // 2))
    return frame


class Recorder:
    def __init__(self, out, title):
        self.out, self.title = Path(out).resolve(), str(title)
        self._lock, self._stop = threading.Lock(), threading.Event()
        self._thread = None
        self._error = None
        self._rows, self._events = [], []
        self._event = dict(stage="Starting recording", call="", result="", pid=None, prefix=None, event_id=0)

    def set_event(self, stage, call, result="", pid=None, prefix=None):
        if pid is not None and (type(pid) is not int or pid <= 0):
            raise ValueError("pid must identify the owned Session")
        if prefix is not None and (not isinstance(prefix, str) or not prefix.strip()):
            raise ValueError("prefix must be a nonempty project title")
        if not isinstance(result, str):
            result = json.dumps(result, ensure_ascii=False, default=str)
        with self._lock:
            self._event = dict(stage=str(stage), call=str(call), result=result, pid=pid,
                               prefix=prefix, event_id=len(self._events) + 1)
            self._events.append(dict(self._event, utc=datetime.now(timezone.utc).isoformat(),
                                     monotonic=time.perf_counter()))

    def start(self):
        if self._thread is not None:
            if self._stop.is_set():
                raise RuntimeError("A completed Recorder cannot be restarted")
            return self
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "raw").mkdir(exist_ok=False)
        (self.out / "frames").mkdir(exist_ok=False)
        self._log = (self.out / "frames.jsonl").open("x", encoding="utf-8")
        self._start = time.perf_counter()
        self._start_utc = datetime.now(timezone.utc).isoformat()
        self._thread = threading.Thread(target=self._run, name="passive-proteus-recorder", daemon=True)
        self._thread.start()
        return self

    def _capture(self):
        with self._lock:
            event = dict(self._event)
        started = time.perf_counter()
        stamp = datetime.now(timezone.utc).isoformat()
        native, dialogs, error = None, [], None
        if event["pid"] is not None or event["prefix"] is not None:
            try:
                native, dialogs = _observe.capture(pid=event["pid"], prefix=event["prefix"])
            except (OSError, RuntimeError) as exc:
                error = f"{type(exc).__name__}: {exc}"
        captured = time.perf_counter()
        index = len(self._rows)
        filename = f"{index:06d}.png"
        raw = None
        if native is not None:
            raw = f"raw/{filename}"
            native.save(self.out / raw, compress_level=3)
        _display(self.title, native, event).save(self.out / "frames" / filename, compress_level=3)
        row = dict(index=index, utc=stamp, elapsed_seconds=started - self._start,
                   capture_seconds=captured - started, event=event, dialogs=dialogs,
                   capture_error=error, raw=raw, frame=f"frames/{filename}",
                   native_size=list(native.size) if native is not None else None)
        self._rows.append(row)
        self._log.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._log.flush()

    def _run(self):
        try:
            deadline = time.perf_counter()
            while not self._stop.is_set():
                self._capture()
                deadline = max(deadline + 1 / FPS, time.perf_counter())
                self._stop.wait(max(0, deadline - time.perf_counter()))
        except BaseException as exc:
            self._error = exc
            self._stop.set()

    def stop(self):
        if self._thread is None or not hasattr(self, "_log") or self._log.closed:
            return
        self._stop.set()
        self._thread.join()
        try:
            if self._error is None:
                self._capture()  # Include the latest event even if stop follows it immediately.
        finally:
            self._log.close()
        duration = time.perf_counter() - self._start
        with self._lock:
            events = [dict(item, elapsed_seconds=item["monotonic"] - self._start) for item in self._events]
        report = dict(title=self.title, started_utc=self._start_utc, requested_fps=FPS,
                      duration_seconds=duration, frame_count=len(self._rows),
                      raw_frame_count=sum(row["raw"] is not None for row in self._rows),
                      actual_fps=len(self._rows) / duration, events=events,
                      error=str(self._error) if self._error else None,
                      capture_errors=sum(row["capture_error"] is not None for row in self._rows))
        (self.out / "recording.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if self._error is not None:
            raise RuntimeError("Passive recording failed; retained available frames") from self._error

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


def encode(out, destination):
    """Keep every native-window frame in order and remove windowless waiting time."""
    out, destination = Path(out).resolve(), Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    report = json.loads((out / "recording.json").read_text(encoding="utf-8"))
    assert report["error"] is None, report["error"]
    rows = [json.loads(line) for line in (out / "frames.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == report["frame_count"] and rows
    assert [row["index"] for row in rows] == list(range(len(rows)))
    assert all(a["elapsed_seconds"] <= b["elapsed_seconds"] for a, b in zip(rows, rows[1:]))
    source_count = len(rows)
    for index, row in enumerate(rows):
        end = rows[index + 1]["elapsed_seconds"] if index + 1 < len(rows) else report["duration_seconds"]
        row["source_duration_seconds"] = end - row["elapsed_seconds"]
    rows = [row for row in rows if row["raw"] is not None]
    if not rows:
        raise ValueError("No native-window frames to encode")
    with Image.open(out / rows[0]["raw"]) as source:
        native_size = source.size
    size = (1280, round(native_size[1] * 1280 / native_size[0]))
    # All retained frames contribute to one palette; small tiles keep generation bounded.
    tiles = Image.new("RGB", (16 * 64, ((len(rows) + 15) // 16) * 48), "#0e1623")
    for index, row in enumerate(rows):
        with Image.open(out / row["raw"]) as source:
            tiles.paste(source.resize((64, 48)), ((index % 16) * 64, (index // 16) * 48))
    palette = tiles.quantize(colors=126, method=Image.Quantize.MEDIANCUT)
    # Full-size LED source frames contain this yellow and black; small tiles miss the lit glyph.
    palette.putpalette(palette.getpalette()[:126 * 3] + [255, 255, 28, 0, 0, 0])
    frames, durations, participation = [], [], []
    previous_tick = 0
    retained_seconds = 0
    for row in rows:
        with Image.open(out / row["raw"]) as source:
            assert source.size == native_size, "Native window dimensions changed during capture"
            # Resize the complete native interface; no presentation shell or captions.
            display = source.convert("RGB").resize(size, Image.Resampling.LANCZOS)
            frames.append(display.quantize(palette=palette, dither=Image.Dither.NONE))
        retained_seconds += row["source_duration_seconds"]
        tick = max(previous_tick + 1, round(retained_seconds / SPEED * 100))
        milliseconds = (tick - previous_tick) * 10
        previous_tick = tick
        durations.append(milliseconds)
        participation.append(dict(index=row["index"], source=row["raw"], raw=row["raw"],
                                  elapsed_seconds=row["elapsed_seconds"],
                                  source_duration_seconds=row["source_duration_seconds"],
                                  gif_duration_ms=milliseconds))
    durations[-1] += 2000
    destination.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(destination, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, disposal=1, optimize=True, comment=b"Native interface only; waits removed; 6x; final hold +2s")
    with Image.open(destination) as gif:
        actual_duration = 0
        for index in range(gif.n_frames):
            gif.seek(index)
            actual_duration += gif.info["duration"]
        gif_frames = gif.n_frames
    assert actual_duration == sum(durations)
    manifest = dict(recording=str(out), gif=destination.name, source_frame_count=source_count,
                    retained_frame_count=len(rows), omitted_waiting_frame_count=source_count - len(rows),
                    retained_duration_seconds=retained_seconds,
                    gif_frame_count=gif_frames, all_source_frames_used=len(rows) == source_count,
                    all_native_frames_used=True, waiting_segments_removed=True, speed=SPEED,
                    final_hold_added_ms=2000, duration_ms=actual_duration, size=list(size),
                    native_interface_only=True,
                    palette_colors=128, optimize=True,
                    reserved_palette_colors=[[255, 255, 28], [0, 0, 0]],
                    bytes=destination.stat().st_size, under_10_mb=destination.stat().st_size <= 10 * 1024 * 1024,
                    sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                    recording_duration_seconds=report["duration_seconds"], actual_capture_fps=report["actual_fps"],
                    frames=participation)
    destination.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("encode", "selfcheck"))
    parser.add_argument("out")
    parser.add_argument("destination", nargs="?")
    args = parser.parse_args()
    if args.command == "encode":
        assert args.destination, "Provide the GIF destination"
        result = encode(args.out, args.destination)
    else:
        # Exercise capture timing, event safety, Unicode wrapping and empty-export rejection
        # without selecting a PID/prefix, so this check cannot capture any application.
        with Recorder(args.out, "Passive recorder self-check / 被动录制检查") as recorder:
            recorder.set_event("No application selected", "Recorder.selfcheck()", "Waiting card only")
            time.sleep(0.55)
            recorder.set_event("Complete", "Recorder.stop()", "Long result: " + "源帧参与验证 " * 45)
            time.sleep(0.2)
        recording = json.loads((Path(args.out) / "recording.json").read_text(encoding="utf-8"))
        assert recording["frame_count"] >= 3 and recording["raw_frame_count"] == 0
        try:
            encode(args.out, Path(args.out) / "selfcheck.gif")
        except ValueError as exc:
            assert str(exc) == "No native-window frames to encode"
        else:
            raise AssertionError("A waiting-only recording must not produce a GIF")
        result = dict(frame_count=recording["frame_count"], waiting_only_export_rejected=True)
    print(json.dumps({key: value for key, value in result.items() if key != "frames"}, indent=2))
