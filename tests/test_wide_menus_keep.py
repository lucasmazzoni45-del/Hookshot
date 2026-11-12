"""Ultrawide menus at Centred keep the loading fade over the whole picture (issue #2220).

The Centred row cleared keep-bit 3 with the pause menu's bit 1 (kMenus = 0xa), and bit 3 is the loading screen's fade
(vtable main+0x4be7b30): the fade was squeezed into the middle 16:9 and the world showed at the sides. Only the menus' bit 1
is cleared now. Source checks, no game or GPU.

python -I -B tests/test_wide_menus_keep.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def need(cond, what):
    if not cond:
        raise SystemExit("FAIL: " + what)


def main():
    fg = (ROOT / "gpu" / "vk" / "vk_framegen.cpp").read_text(encoding="utf-8")
    m = re.search(r"constexpr\s+uint32_t\s+kMenus\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*;", fg)
    need(m, "vk_framegen.cpp has no kMenus")
    menus = int(m.group(1), 0)
    need(menus == 0x2, "kMenus is %#x, not 0x2 (only the pause / map menus' bit 1)" % menus)
    use = re.search(r"host->wide_menus\(opts\.wide_menus \? 0xfu & ~kMenus : 0xfu\)", fg)
    need(use, "wide_sides() no longer clears kMenus from 0xf when Centred")
    need(((0xf & ~menus) >> 3) & 1, "keep-bit 3 (the loading fade) is cleared at Centred")
    need(((0xf & ~menus) & 0x7) == 0x5, "bits 0 and 2 must stay kept, bit 1 cleared")

    wide = (ROOT / "nx2" / "oot_wide.py").read_text(encoding="utf-8")
    kv = re.search(r"KEEP_VTABLES\s*=\s*\(([^)]*)\)", wide)
    need(kv, "oot_wide.py has no KEEP_VTABLES")
    entries = [e.strip() for e in kv.group(1).split(",") if e.strip()]
    need(len(entries) == 4, "KEEP_VTABLES has %d entries, not 4" % len(entries))
    need(entries[3] == "MAIN + 0x4be7b30", "KEEP_VTABLES[3] is %s, not the loading fade 0x4be7b30" % entries[3])
    comment = wide[:kv.start()]
    need(re.search(r"bit 3, the loading\s+# fade \(main\+0x4be7b30\)", comment), "oot_wide.py's comment does not name bit 3 as the loading fade")
    need("clears the menus' bit 1 (" in comment, "oot_wide.py's comment does not say the menus are bit 1 alone")

    host = (ROOT / "host" / "hos_main.c").read_text(encoding="utf-8")
    need("3 loading fade" in host, "hos_main.c's hos_wide_keep_mask comment does not name bit 3")
    print("PASS: Centred menus clear only keep-bit 1; the loading fade (bit 3) covers the whole picture")


if __name__ == "__main__":
    main()
