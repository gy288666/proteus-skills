"""Check ELF/HEX equality, Intel HEX checksums, memory bounds and boot vectors."""
from pathlib import Path
import struct


def check(stem):
    stem = Path(stem)
    elf = stem.with_suffix(".elf").read_bytes()
    assert elf[:7] == b"\x7fELF\x01\x01\x01"
    assert struct.unpack_from("<H", elf, 18)[0] == 40
    entry, phoff = struct.unpack_from("<II", elf, 24)
    phsize, phcount = struct.unpack_from("<HH", elf, 42)
    elf_image = {}
    for index in range(phcount):
        kind, offset, _, physical, size, memory_size, _, _ = struct.unpack_from(
            "<8I", elf, phoff + index * phsize)
        if kind == 1:
            assert size == memory_size and 0x08000000 <= physical < physical + size <= 0x08001000
            assert offset + size <= len(elf)
            elf_image.update((physical + i, value) for i, value in enumerate(elf[offset:offset + size]))

    hex_image, base, ended = {}, 0, False
    for line in stem.with_suffix(".hex").read_text(encoding="ascii").splitlines():
        assert line.startswith(":") and not ended
        record = bytes.fromhex(line[1:])
        assert len(record) == record[0] + 5 and sum(record) % 256 == 0
        kind, offset = record[3], int.from_bytes(record[1:3], "big")
        payload = record[4:-1]
        if kind == 0:
            for i, value in enumerate(payload):
                address = base + offset + i
                assert address not in hex_image
                hex_image[address] = value
        elif kind == 4:
            assert len(payload) == 2 and offset == 0
            base = int.from_bytes(payload, "big") << 16
        elif kind == 5:
            assert len(payload) == 4 and offset == 0 and int.from_bytes(payload, "big") == entry
        elif kind == 1:
            assert not payload and offset == 0
            ended = True
        else:
            raise AssertionError(f"Unexpected HEX record {kind}")
    assert ended and elf_image and elf_image == hex_image
    stack, reset = struct.unpack("<II", bytes(elf_image[0x08000000 + i] for i in range(8)))
    assert stack == 0x20001000 and reset == entry and reset & 1
    assert (reset & ~1) in elf_image
    return {"image_bytes": len(elf_image), "stack": hex(stack), "reset": hex(reset), "elf_hex_match": True}


if __name__ == "__main__":
    for name in ("hold", "toggle", "dual"):
        print(name, check(Path(__file__).resolve().parent / name))
