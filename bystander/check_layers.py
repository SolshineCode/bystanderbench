#!/usr/bin/env python3
"""Refuse a capture directory in which any requested layer came back all zeros.

WHY (§F139). `extract_resid` selects layers by matching tensor names it happens to see
(`st->layers.count(layer)`), so a layer that is never emitted is silently absent rather than an
error, and the slot is written as zeros. On 2026-09-13 an Olmo capture asked for `l_out-31`
from a 32-block model, got a full block of zeros, and passed every check anyone would think to
run: 4 bins, the exact expected byte size, the right `d_model`, no NaN, and a non-zero total.
One layer of eight was dead.

So the checks that look sufficient are not. Size proves the shape was allocated. `d_model`
proves the config was read. Absence of NaN proves nothing at all about a zero. The only thing
that catches this is asking, per layer, whether anything is in there.

Exits 1 and names the dead layers if any bin has one. Meant to run straight after
`extract_resid`, where a refusal costs one re-run instead of a silent hole in the corpus.

SECOND CHECK, added 2026-09-13 (§F156). The above asks whether the layers you GOT are alive.
It cannot ask whether you got the layers you ASKED FOR, because a layer that was never
written is not a zero layer -- there is nothing for it to look at. The lightning capture
requested seven layers, received three, and passed this file cleanly; the shortfall surfaced
three stages later in the HF packager's size assert, by luck.

So the directory may also carry `requested_layers.txt`, written by whatever invoked
`extract_resid` from the SAME shell variable it passed as RESID_LAYERS. When that file is
present, every sidecar's layer list must equal it or this exits 1. One source of truth, so
the check cannot be satisfied by typing the same wrong number twice.

Usage:  python bystander/check_layers.py bystander/acts_<tag>
        # optional, overrides the file:
        python bystander/check_layers.py --expect 8,24,40 bystander/acts_<tag>
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np


def check(d: Path, expect: list[int] | None = None) -> int:
    bins = sorted(d.glob("acts/*.bin"))
    if not bins:
        print(f"{d.name}: no .bin files to check")
        return 1
    # §F156: what was asked for, if anyone recorded it.
    if expect is None:
        f = d / "requested_layers.txt"
        if f.is_file():
            expect = [int(x) for x in f.read_text().replace(",", " ").split()]
    bad, checked = {}, 0
    for b in bins:
        side = b.with_suffix(".json")
        if not side.is_file():
            print(f"{d.name}: {b.name} has no sidecar, cannot know its layer set")
            return 1
        meta = json.loads(side.read_text())
        layers, dm = meta["layers"], meta["d_model"]
        if expect is not None and list(layers) != list(expect):
            missing = sorted(set(expect) - set(layers))
            extra = sorted(set(layers) - set(expect))
            print(f"{d.name}: REFUSED. {b.name} holds layers {list(layers)} but "
                  f"{list(expect)} were requested."
                  + (f" Missing: {missing}." if missing else "")
                  + (f" Unexpected: {extra}." if extra else "")
                  + " extract_resid drops layers whose tensor names it does not see and says"
                    " nothing (§F156). Either re-extract with a layer set this model actually"
                    " emits, or record the delivered set as the requested one and say so on"
                    " the dataset card.")
            return 1
        a = np.fromfile(b, dtype=np.float32)
        if a.size != len(layers) * 3 * dm:
            print(f"{d.name}: {b.name} is {a.size} floats, expected "
                  f"{len(layers)*3*dm} for {len(layers)} layers x 3 slots x {dm}")
            return 1
        a = a.reshape(len(layers), 3, dm)
        dead = [layers[i] for i in range(len(layers)) if not a[i].any()]
        checked += 1
        if dead:
            bad.setdefault(tuple(dead), []).append(b.name)
    if bad:
        print(f"REFUSING {d.name}: {sum(len(v) for v in bad.values())} of {checked} bins have "
              f"an all-zero layer.")
        for dead, names in bad.items():
            print(f"  layers {list(dead)} dead in {len(names)} bin(s), e.g. {names[0]}")
        print("  A requested layer that the model never emits is written as zeros rather than "
              "refused.\n  Check the tensor actually exists for this architecture and re-run "
              "with a layer set that does.")
        return 1
    print(f"{d.name}: {checked} bins, no all-zero layers")
    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    expect = None
    # `--expect L` may appear before or after the directories. Until 2026-09-15 only the
    # leading position was parsed; `dir --expect L` silently treated "--expect" and "L" as
    # directories, printed "no .bin files to check" and exited 1, which §F169 misread as a
    # glob quirk and §F172 traced to this. Either order now means the same thing.
    if "--expect" in argv:
        i = argv.index("--expect")
        if i + 1 >= len(argv):
            raise SystemExit("--expect needs a comma list, e.g. --expect 8,24,40")
        expect = [int(x) for x in argv[i + 1].replace(",", " ").split()]
        argv = argv[:i] + argv[i + 2:]
    if not argv:
        raise SystemExit("usage: check_layers.py [--expect L1,L2,...] <acts dir> [<acts dir> ...]")
    raise SystemExit(max(check(Path(x), expect) for x in argv))
