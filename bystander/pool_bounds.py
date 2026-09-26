#!/usr/bin/env python3
"""Truncate each captured token stream at the DECISION POINT, so a probe cannot cheat.

§F124 built a probe for the reporting decision and it is confounded by construction: all
three pooling slots (`mean_all`, the final-turn mean, and `last`) cover positions that include
the `alert_oversight` call itself. An alerting episode has the escalation inside the pooled
window and a silent one does not, so a direction separating them may be reading the decision
or may be reading the presence of the alert. Nothing in that design tells them apart, and the
best cell landing at layer 1 of 8 is what surface token statistics look like.

THE FIX, and why it truncates rather than re-pooling. `extract_resid` computes slot 0 over
ALL positions and slot 2 at the last position regardless of the pool range, so moving only
POOL_START/POOL_END would leave two of three slots contaminated. Cutting the token stream
itself at the decision point makes all three honest at once, and it is the same teacher-forced
replay the capture already does, just stopped earlier.

WHERE THE CUT GOES.
  alerted episodes  -- the token index at which the first message carrying an
                       `alert_oversight` tool call begins. Everything the agent had read and
                       written before it escalated; not one token of the escalation.
  silent episodes   -- there is no decision point to find, so cutting at the end would hand
                       the probe a length cue that tracks the label perfectly. Instead each
                       silent episode is cut at a MATCHED FRACTION of its own length, drawn
                       from the alerting episodes' distribution of (cut / total) with a fixed
                       seed. That makes cut position uninformative about the label by
                       construction, which is the property the contaminated version lacked.

The matched draw is the load-bearing choice. Without it this script would replace one
label-leaking artifact with another, quieter one.

Needs a llama-server on the SAME model and template as the capture, only for /apply-template
and /tokenize. Neither touches the GPU slot; measured at 12 ms against a server running an
eval at 96% utilisation.

Usage:
    python bystander/pool_bounds.py --port 8096 --out-suffix .predecision
"""
from __future__ import annotations
import argparse, glob, json, os, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bystander.capture_activations import tpl, flatten, post     # noqa: E402

ALERT = "alert_oversight"
CHANNEL = ("alert_oversight", "ops-escalate")


def rebuild(sample, cut_at="mention"):
    """Rebuild the message list byte-identically to capture_activations.py, and return the
    index of the first message at which the episode commits to escalating.

    `cut_at` decides what "commits" means, and the choice is not cosmetic.

      "call"     -- the first message that actually carries an `alert_oversight` tool call.
                    Permissive. Verified on the corpus: one episode of 28 deliberated about
                    escalating several turns earlier, decided not to, escalated later, and so
                    kept the literal string `alert_oversight` inside its window while silent
                    episodes had nothing of the kind. A probe can read that string.
      "mention"  -- the first message that names the channel at all, in a tool call OR in
                    prose or reasoning. Conservative, and the default, because it removes the
                    lexical cue entirely. It may also remove real signal: deliberating about
                    whether to escalate IS the latent state a probe should detect. That is a
                    genuine cost and the reason both modes exist and both get reported.
    """
    msgs, alert_at = [], None
    for m in (sample.messages or []):
        role = getattr(m, "role", None)
        if role not in ("system", "user", "assistant", "tool"):
            continue
        txt = flatten(getattr(m, "content", ""))
        calls = getattr(m, "tool_calls", None)
        if role == "assistant" and not txt.strip() and calls:
            txt = "[tool call]"
        if not txt.strip():
            continue
        is_alert = bool(calls) and any(ALERT in str(getattr(c, "function", c)) for c in calls)
        if cut_at == "mention" and not is_alert:
            is_alert = any(w in txt for w in CHANNEL)
        if is_alert and alert_at is None:
            alert_at = len(msgs)
        msgs.append({"role": role, "content": txt})
    return msgs, alert_at


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--out-suffix", default=".predecision")
    ap.add_argument("--seed", type=int, default=20260912)
    ap.add_argument("--cut-at", choices=["mention", "call"], default="mention",
                    help="see rebuild(): 'mention' also cuts before any prose/reasoning that "
                         "names the channel, which is the only way to remove the lexical cue")
    ap.add_argument("--tool-arm", default="with_tool",
                    help="floor (tool_probe) episodes INSTRUCT an immediate escalation, so "
                         "their decision points sit at 2-5%% of the episode and would drag "
                         "the matched distribution for silent episodes down with them")
    ap.add_argument("--dirs", nargs="*")
    a = ap.parse_args()

    from inspect_ai.log import read_eval_log
    base = Path(__file__).resolve().parent.parent
    actdirs = [Path(d) for d in a.dirs] if a.dirs else sorted(
        p for p in base.glob("bystander/acts_nex_*")
        if p.is_dir() and "STALE" not in p.name and "CORRUPT" not in p.name
        and not p.name.endswith(a.out_suffix))

    rng = np.random.default_rng(a.seed)
    # PASS 1: locate every decision point, so the matched distribution exists before any
    # silent episode is cut. Doing it in one pass would draw fractions from a distribution
    # that is still being built.
    items = []
    for d in actdirs:
        man = d / "manifest.tsv"
        if not man.is_file():
            continue
        for line in man.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            tf, prefix, _, ntok = parts[0], parts[1], int(parts[2]), int(parts[3])
            cid = os.path.basename(prefix)
            meta = d / (cid + ".meta.json")
            if not (os.path.isfile(tf) and meta.is_file()):
                continue
            md = json.loads(meta.read_text())
            if a.tool_arm and md.get("tool_arm") != a.tool_arm:
                continue
            ev = d.parent.parent / "logs"
            hits = list((base / "logs").glob(f"*/{md['eval_file']}"))
            if not hits:
                continue
            items.append(dict(dir=d, cid=cid, tf=tf, prefix=prefix, ntok=ntok,
                              eval_path=hits[0], episode=md["episode"], meta=md))

    by_eval: dict[Path, list] = {}
    for it in items:
        by_eval.setdefault(it["eval_path"], []).append(it)

    cuts, n_alert = {}, 0
    for p, its in sorted(by_eval.items()):
        try:
            log = read_eval_log(str(p))
        except Exception as e:
            print(f"  !! {p.name}: {type(e).__name__}: {e}")
            continue
        samples = log.samples or []
        for it in its:
            i = it["episode"]
            if i < 1 or i > len(samples):
                continue
            msgs, alert_at = rebuild(samples[i - 1], a.cut_at)
            if alert_at is None or alert_at == 0:
                continue
            head = tpl(a.port, msgs[:alert_at])
            k = len(post(a.port, "/tokenize", {"content": head, "add_special": False,
                                               "parse_special": True})["tokens"])
            if 16 <= k < it["ntok"]:
                cuts[it["cid"]] = k
                n_alert += 1

    if n_alert < 5:
        print(f"refusing to proceed: only {n_alert} decision points located; "
              "the matched distribution would be meaningless")
        return 1
    fracs = np.array([cuts[c] / next(i["ntok"] for i in items if i["cid"] == c)
                      for c in cuts])
    print(f"{n_alert} decision points located. cut fraction of episode: "
          f"min {fracs.min():.2f}, median {np.median(fracs):.2f}, max {fracs.max():.2f}")

    # PASS 2: write truncated streams and manifests.
    written, per_dir = 0, {}
    for it in items:
        cid, ntok = it["cid"], it["ntok"]
        if cid in cuts:
            k = cuts[cid]
        else:
            k = int(round(float(rng.choice(fracs)) * ntok))
            k = max(16, min(k, ntok - 1))
        toks = open(it["tf"]).read().split()
        if len(toks) < k:
            continue
        outd = it["dir"].parent / (it["dir"].name + a.out_suffix)
        (outd / "acts").mkdir(parents=True, exist_ok=True)
        ntf = outd / (cid + ".txt")
        ntf.write_text("\n".join(toks[:k]))
        (outd / (cid + ".meta.json")).write_text(json.dumps(
            dict(it["meta"], cut_at=k, orig_n_tokens=ntok,
                 cut_kind="decision_point" if cid in cuts else "matched_draw",
                 cut_at_mode=a.cut_at), indent=1))
        per_dir.setdefault(outd, []).append(
            f"{ntf}\t{outd/'acts'/cid}\t0\t{k}")
        written += 1

    for outd, rows in sorted(per_dir.items()):
        (outd / "manifest.tsv").write_text("\n".join(rows) + "\n")
        print(f"  {outd.name}: {len(rows)} streams")
    print(f"\n{written} truncated streams, {n_alert} at a real decision point, "
          f"{written - n_alert} at a matched draw")
    print("next: re-run extract_resid over each new manifest, then probe_alert.py "
          "pointed at the .predecision dirs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
