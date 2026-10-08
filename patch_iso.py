#!/usr/bin/env python3
"""Ape Escape 2 (USA, SLUS-20685) - Quick Gadget Swap restore, ISO patcher.

Writes a *patched copy* of the ISO (the original is never modified).
  python3 patch_iso.py "Ape Escape 2 (USA).iso" "Ape Escape 2 (USA) [QuickSwap].iso"
  python3 patch_iso.py --check "Ape Escape 2 (USA).iso"      # read-only verification

Note: a patched ELF has a different CRC in PCSX2, so PCSX2's GameDB fix for CRC BDD9F5E1
(COP2 timing) stops applying automatically. On PCSX2 prefer the .pnach; use this for real
hardware / OPL.
"""
import shutil, struct, sys

ELF_NAME = b'SLUS_206.85;1'
TEXT_VADDR, TEXT_FOFF = 0x00100000, 0x1000
# (EE address, original word, patched word)
PATCH = [
    (0x002B4B10, 0x16000053, 0x16004711),
    (0x002C6758, 0x27BDFFF0, 0x82230B3E),
    (0x002C675C, 0xFFB00000, 0x14600018),
    (0x002C6760, 0xFFBF0008, 0x24020001),
    (0x002C6764, 0x0C0B0C96, 0x3C02003B),
    (0x002C6768, 0x0000202D, 0x2404001E),
    (0x002C676C, 0x0C0B0DB2, 0x8C432118),
    (0x002C6770, 0x0040802D, 0x10640013),
    (0x002C6774, 0x54400006, 0x24020001),
    (0x002C6778, 0x8E040F98, 0x8E230B0C),
    (0x002C677C, 0x2402FFFF, 0x00121080),
    (0x002C6780, 0x70401389, 0xAE320B10),
    (0x002C6784, 0x2402FFFF, 0x00511021),
    (0x002C6788, 0x1000000F, 0xAE230B6C),
    (0x002C678C, 0xDFB00000, 0x24050001),
    (0x002C6790, 0x8C830030, 0xAE320B0C),
    (0x002C6794, 0x48220000, 0x24040002),
    (0x002C6798, 0x700214A8, 0xAE200B60),
    (0x002C679C, 0xD86502A0, 0x8C430AFC),
    (0x002C67A0, 0xD86602B0, 0xAE200B64),
    (0x002C67A4, 0xD86702C0, 0xA2250B3E),
    (0x002C67A8, 0xD86802D0, 0xAE230B70),
    (0x002C67AC, 0x48A20800, 0xA2200B3F),
    (0x002C67B0, 0x4BE129BC, 0x0C06DE70),
    (0x002C67B4, 0x4BE130BD, 0xAE230B74),
    (0x002C67B8, 0x4BE138BE, 0x080AD318),
    (0x002C67BC, 0x4BE1404B, 0x0000102D),
    (0x002C67C0, 0x48220800, 0x080AD318),
    (0x002C67C4, 0xDFB00000, 0x00000000)
]

def find_elf(f):
    f.seek(16 * 2048); pvd = f.read(2048)
    if pvd[1:6] != b'CD001': sys.exit('not an ISO9660 image')
    lba, size = struct.unpack_from('<I', pvd, 156 + 2)[0], struct.unpack_from('<I', pvd, 156 + 10)[0]
    f.seek(lba * 2048); d = f.read(size); i = 0
    while i < len(d):
        n = d[i]
        if n == 0: i = (i // 2048 + 1) * 2048; continue
        name = d[i + 33:i + 33 + d[i + 32]]
        if name == ELF_NAME:
            return struct.unpack_from('<I', d, i + 2)[0] * 2048, struct.unpack_from('<I', d, i + 10)[0]
        i += n
    sys.exit('SLUS_206.85 not found - is this Ape Escape 2 (USA)?')

def offsets(f):
    base, size = find_elf(f)
    return [(base + a - TEXT_VADDR + TEXT_FOFF, a, o, p) for a, o, p in PATCH], base, size

def check(path):
    with open(path, 'rb') as f:
        offs, base, size = offsets(f); state = set()
        for off, a, o, p in offs:
            f.seek(off); w = struct.unpack('<I', f.read(4))[0]
            state.add('orig' if w == o else 'patched' if w == p else 'unknown')
            if w not in (o, p): print('mismatch @%08X: %08X (expected %08X)' % (a, w, o))
    print('ELF at ISO offset 0x%X (%d bytes): %s' % (base, size, ', '.join(sorted(state))))
    return state

def main():
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == '--check': check(a[1]); return
    if len(a) != 2: sys.exit(__doc__)
    src, dst = a
    if check(src) != {'orig'}: sys.exit('source is not an unmodified SLUS-20685 ISO; aborting')
    print('copying ...'); shutil.copyfile(src, dst)
    with open(dst, 'r+b') as f:
        offs, _, _ = offsets(f)
        for off, ad, o, p in offs: f.seek(off); f.write(struct.pack('<I', p))
    print('done:', dst); check(dst)

if __name__ == '__main__':
    main()
