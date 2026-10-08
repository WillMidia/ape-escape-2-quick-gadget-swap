# Ape Escape 2 (USA) - Quick Gadget Swap restored

Restores to the North American release (SLUS-20685, CRC `BDD9F5E1`) the quick gadget swap that
only existed in the Japanese release (Saru! Get You! 2, SCPS-15025).

## In-game usage

1. Press the face button (△ ○ ✕ □) of the gadget you are **already holding** again.
   The "roulette" opens next to that button.
2. Keep pressing the same button to move to the next gadget. It is equipped immediately,
   and the ones you don't have yet (shown as "?") are skipped.
3. To confirm, **use the gadget (right analog stick)** or press **R3**. The gadget is
   saved to that button; if it was already on another button, the two swap places.
4. If you press **another** face button, the roulette closes and you switch to that button.
   The chosen gadget is only saved if it isn't already on another button.

This is the original JP behavior: only the opening code was reinserted, everything else is code
that was already on the US disc.

## Files

| File | Purpose |
|---|---|
| `SLUS-20685_BDD9F5E1.pnach` | Patch for PCSX2 (**recommended**). Copy it to PCSX2's `patches/` folder (e.g. `~/.config/PCSX2/patches/` on Linux) and enable it in Game Properties → Patches. |
| `patch_iso.py` | Creates a patched **copy** of the ISO (for real PS2 / OPL). `--check` only verifies. |

Why prefer the pnach on PCSX2: modifying the ELF changes the game's CRC, so PCSX2 stops
automatically applying the COP2 timing fix that its GameDB has for `BDD9F5E1`. Old savestates
(named by CRC) also stop showing up. The pnach has none of these problems and works with old
savestates, because it uses `patch=1` and is continuously reapplied.

```
python3 patch_iso.py "Ape Escape 2 (USA).iso" "Ape Escape 2 (USA) [QuickSwap].iso"
python3 patch_iso.py --check "Ape Escape 2 (USA).iso"
```

## What was removed in the western release

Player object (USA) at `0x4D4220`:
- `+0xAFC..+0xB08`: △ ○ ✕ □ slots
- `+0xB0C`: current slot
- `+0xB14`: current gadget
- `+0xB3E`: roulette open flag
- `+0xB6C`: slot being edited
- `+0xB70`: selection
- `+0xB74`: original gadget

| | USA | JP |
|---|---|---|
| Face button handler (identical) | `0x2B4960` | `0x2ADD48` |
| Open/close roulette | `0x2B4AE8` (**100 instr.**) | `0x2ADED0` (**128 instr.**) |
| Per-frame roulette update (identical) | `0x2B4CC8` | `0x2AE120` |
| Roulette HUD (identical) | `0x243608` | `0x23DB18` |
| Stage ID (the roulette is blocked on stage `0x1E`) | `0x3B2118` | `0x3AA518` |

The handler, identical in both versions, calls `open_close(1, slot)` when the pressed button is
the current slot's. In the US build, the `a0 != 0` branch of that function became just
`bnez $s0, return 1`: the 26 instructions that set `+0xB3E` and filled `+0xB6C/B70/B74` were
removed. Everything else (cycling, skipping unowned gadgets, HUD with "?", confirm/swap, writing
to the save at `0x3E0694`) remained on the disc.

What the patch does:
- `0x2B4B10`: `bnez $s0, 0x2C6758`. The delay slot `addiu $v0,$zero,1` is kept.
- `0x2C6758..0x2C67C4`: the original JP branch (addresses adjusted: SFX `0x1B79C0`, stage `0x3B2118`),
  returning to the epilogue at `0x2B4C60`. The cave reuses a dead function (no
  `jal`/`j`/pointer to it anywhere in the ELF or in RAM).

## How it was verified

- Structural diff of the ~6700 JP×USA functions (rabbitizer/R5900). The helper functions are
  identical; the only difference in the gadget logic is the removed branch.
- The ISO path was checked at byte level (the 29 original words match at the offsets). It writes
  the same words as the tested pnach, but it hasn't been played from a fresh boot.
