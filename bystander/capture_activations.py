#!/usr/bin/env python3
"""Turn finished BystanderBench episodes into token streams for activation capture.

Why this exists. The benchmark talks to a llama-server over the OpenAI API and captures
nothing internal, so every result so far is purely behavioural. The justification for this
benchmark living in a probing repo is that a behavioural measure cannot separate a silent
agent from an oblivious one, and separating them needs activations. This closes that gap.

What it does. For each episode it rebuilds the exact conversation as rendered by the
serving template, then writes the token stream plus an `extract_resid` manifest so the
episode can be replayed through the same GGUF and its residual stream recorded.

Provenance grade: **teacher-forced**, like everything else in this project's activation
pipeline. It is a replay, not the generating forward pass. The weights and quantisation
match the server that produced the episode as long as `--port` points at the SAME model,
which the script records in the sidecar so a mismatch is visible later.

Pooling slot: by default the pooled range covers the assistant's FINAL turn, which is the
decision point the benchmark scores. `--pool-from-discovery` instead pools from the first
message in which evidence content appears, which is the span where a bystander decision
would have to be taken. Both are written to the sidecar so an analysis can choose.
"""
import argparse, glob, json, os, sys, urllib.request
from pathlib import Path

# Repo root from this file, not an absolute path (2026-09-12). The GGUFs this replays
# through are public Hugging Face downloads, so nothing here is machine-specific once the
# path is derived rather than written down.
BASE = str(Path(__file__).resolve().parent.parent)


def post(port, path, obj, timeout=600):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                 data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _diagnose_http_error(e):
    """Decode a POST HTTPError's body once, and if it matches the llama-server
    --prefill-assistant guard (2026-09-14, S10 -- see the pool_start comment in main()),
    say so with the actionable fix instead of just echoing the bare status line.
    """
    try:
        body = e.read().decode(errors="replace").strip()
    except Exception:
        body = ""
    if "Cannot continue an assistant message" in body or "2 or more assistant messages" in body:
        return (f"HTTPError {e.code}: server rejects a prefix ending in an assistant/"
                f"tool_calls turn ({body or e}). This llama-server build has "
                "--prefill-assistant on by default (the default); restart the server with "
                "--no-prefill-assistant to capture this episode.")
    return f"HTTPError {e.code}: {body or e}"


def _merge_trailing_assistant(msgs):
    """Collapse a run of trailing assistant turns into one.

    Llama-3.3's template refuses a conversation ending in two or more assistant messages,
    and a tool-calling transcript produces that routinely (the tool-call turn and the turn
    reading the result are both assistant). Faithful for teacher forcing, since those turns
    concatenate in the rendered text anyway. A no-op unless the tail actually has two or
    more, so every capture made before 2026-09-12 renders identically.
    """
    tail = 0
    while tail < len(msgs) and msgs[len(msgs) - 1 - tail]["role"] == "assistant":
        tail += 1
    if tail < 2:
        return msgs
    merged = "\n\n".join(m["content"] for m in msgs[-tail:])
    return msgs[:-tail] + [{"role": "assistant", "content": merged}]


def tpl(port, msgs):
    """Every /apply-template call goes through here so the merge cannot be forgotten."""
    return post(port, "/apply-template", {"messages": _merge_trailing_assistant(msgs)})["prompt"]


def flatten(content):
    """Rebuild the text of a message for teacher-forced replay.

    REASONING PARTS ARE INCLUDED (fixed 2026-09-10). This previously kept only
    `type == "text"` and silently dropped `type == "reasoning"`, so for any model that
    emits chain-of-thought the replay prompt omitted the reasoning the model had actually
    produced. The activations were then extracted over a token sequence the model never
    saw, which destroys the teacher-forcing guarantee that is the whole basis for calling
    tier-2 captures "a replay rather than the generating pass". Silent, and it invalidates
    exactly the reasoning models tier 2 is most interesting on.

    Inspect puts the text in `.reasoning`, or in `.summary` when the provider returns a
    summarised/redacted trace, so both are taken.
    """
    if isinstance(content, str):
        return content
    out = []
    for part in content or []:
        if isinstance(part, str):
            out.append(part)
            continue
        ptype = part.get("type") if isinstance(part, dict) else getattr(part, "type", None)
        if ptype == "text":
            out.append((part.get("text", "") if isinstance(part, dict)
                        else getattr(part, "text", "")) or "")
        elif ptype == "reasoning":
            if isinstance(part, dict):
                txt = (part.get("reasoning") or "") + " " + (part.get("summary") or "")
            else:
                txt = (getattr(part, "reasoning", "") or "") + " " + (getattr(part, "summary", "") or "")
            if txt.strip():
                out.append(txt.strip())
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True,
                    help="llama-server for the SAME model that produced these episodes")
    ap.add_argument("--logdir", action="append", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--eos", default="<|im_end|>")
    ap.add_argument("--pool-from-discovery", action="store_true")
    a = ap.parse_args()

    # Run this with .venv/bin/python. inspect_ai's deps include compiled extensions
    # (pydantic_core) built for that interpreter, so importing them from the pt113 venv
    # fails with ModuleNotFoundError on _pydantic_core. Do not path-hack across venvs.
    from inspect_ai.log import read_eval_log

    os.makedirs(os.path.join(a.out_dir, "acts"), exist_ok=True)
    man, n_skip = [], 0
    seen_cids: dict[str, str] = {}
    for d in a.logdir:
        for p in sorted(glob.glob(os.path.join(d, "*.eval"))):
            log = read_eval_log(p)
            # SKIP FAILED RUNS (2026-09-13, §F133). report.py has always required
            # status == "success"; this loop did not, so a crashed run's partial samples
            # were captured alongside the good run's. Three .eval files sat in
            # logs/bystander-reasoning-nemotron: two status=error with n=1, one
            # status=success with n=12. All three produce cid "..._ep1" because the cid
            # carries the log DIRECTORY but not the log FILE, so the §F22 duplicate guard
            # fired and the whole cell captured 0 of 12. The guard was right; it was being
            # fed runs that should never have reached it.
            if log.status != "success":
                n_skip += len(log.samples or [])
                print(f"skip {os.path.basename(p)}: status={log.status}", flush=True)
                continue
            ta = log.eval.task_args or {}
            arm, tool_arm = ta.get("arm"), ta.get("tool_arm")
            # CID (fixed 2026-09-10). This was `f"{arm}_{tool_arm}_ep{i}"`, with `i`
            # restarting at 1 for every .eval file -- the §F22 design-cell-id bug again,
            # in the one place where a collision silently DESTROYS data rather than only
            # miscounting it, because both rows write the same acts/ path.
            #
            # It had already corrupted a published tree: acts_qwen_backlog/manifest.tsv
            # carried 27 rows against 26 token files with one cid duplicated, and that
            # manifest was copied into hf_upload_labartifacts/ (§F73).
            #
            # The cid now carries the affordance, the solver and the source run directory,
            # and a hard assertion refuses any duplicate rather than trusting the scheme.
            aff = ta.get("affordance", "native")
            solver = ta.get("solver_kind", "tools")
            src = os.path.basename(os.path.normpath(d))
            for i, s in enumerate(log.samples or [], 1):
                cid = f"{src}__{arm}_{tool_arm}_{aff}_{solver}_ep{i}"
                if cid in seen_cids:
                    raise SystemExit(
                        f"capture: duplicate cid {cid!r} (already from {seen_cids[cid]!r}, "
                        f"now from {p!r}). Refusing to overwrite a captured stream. "
                        "This is the bug that corrupted acts_qwen_backlog -- fix the "
                        "inputs rather than removing this check."
                    )
                seen_cids[cid] = p
                msgs = []
                for m in (s.messages or []):
                    role = getattr(m, "role", None)
                    if role not in ("system", "user", "assistant", "tool"):
                        continue
                    txt = flatten(getattr(m, "content", ""))
                    # an assistant turn that only carried tool_calls has empty content;
                    # some templates reject that (§F50), so give it a visible placeholder
                    if role == "assistant" and not txt.strip() and getattr(m, "tool_calls", None):
                        txt = "[tool call]"
                    if not txt.strip():
                        continue
                    out = {"role": role, "content": txt}
                    # 2026-09-13 (§F151). north-mini-code's template does, at line 248,
                    #   message.tool_call_id not in tool_ids_seen.value
                    # for every tool-role turn. We were rebuilding tool turns as bare
                    # {role, content}, so the template raised and the server returned 500
                    # for ALL 18 episodes of that model -- the whole tier-2 corpus for a
                    # model the project cares about, lost to a dropped field rather than to
                    # anything about the episodes. Carry the tool-call identifiers through.
                    # Harmless for templates that ignore them, which is every model
                    # captured before today.
                    tcid = getattr(m, "tool_call_id", None)
                    if role == "tool" and tcid:
                        out["tool_call_id"] = tcid
                    tcs = getattr(m, "tool_calls", None)
                    if role == "assistant" and tcs:
                        rebuilt = []
                        for tc in tcs:
                            fn = getattr(tc, "function", None)
                            name = getattr(fn, "name", None) or getattr(tc, "function", None) or "tool"
                            args = getattr(fn, "arguments", None) if fn is not None else None
                            if args is None:
                                args = getattr(tc, "arguments", None)
                            if not isinstance(args, str):
                                try:
                                    args = json.dumps(args if args is not None else {})
                                except Exception:
                                    args = "{}"
                            rebuilt.append({"id": getattr(tc, "id", None) or name,
                                            "type": "function",
                                            "function": {"name": name if isinstance(name, str) else "tool",
                                                         "arguments": args}})
                        if rebuilt:
                            out["tool_calls"] = rebuilt
                    msgs.append(out)
                # Llama-3.3's template REFUSES a conversation ending in two or more
                # assistant turns ("Cannot have 2 or more assistant messages at the end"),
                # which a tool-calling transcript produces routinely: the tool-call turn and
                # the turn that reads the result are both assistant. Merge only a RUN OF
                # TRAILING assistant turns, which is what the template objects to, and which
                # is faithful for teacher forcing since those turns concatenate in the text
                # anyway. No-op for every model captured before 2026-09-12: the merge only
                # fires when the tail actually has two or more, and prior captures did not.
                # Same class as the §F50 empty-content fix directly above.
                tail = 0
                while tail < len(msgs) and msgs[len(msgs) - 1 - tail]["role"] == "assistant":
                    tail += 1
                if tail >= 2:
                    merged = "\n\n".join(m["content"] for m in msgs[-tail:])
                    msgs = msgs[:-tail] + [{"role": "assistant", "content": merged}]
                if len(msgs) < 2:
                    # 2026-09-13: this was a SILENT skip. On the north-mini backlog it
                    # swallowed 16 of 18 episodes with no reason printed, and the run
                    # reported "wrote 2, skipped 21" with nothing to say which 21 or why.
                    # A skip that cannot be explained is indistinguishable from a bug, and
                    # this corpus's whole permanence argument rests on knowing what was NOT
                    # captured. Say it out loud, with the counts that identify the cause.
                    roles = {}
                    for m in (s.messages or []):
                        roles[getattr(m, "role", "?")] = roles.get(getattr(m, "role", "?"), 0) + 1
                    print(f"skip {cid}: rebuilt to {len(msgs)} usable messages from "
                          f"{len(s.messages or [])} raw ({roles}) -- every turn was empty "
                          f"after flattening, so there is nothing to teacher-force",
                          flush=True)
                    n_skip += 1; continue
                try:
                    prompt = tpl(a.port, msgs)
                    toks = post(a.port, "/tokenize", {"content": prompt,
                                                      "add_special": False,
                                                      "parse_special": True})["tokens"]
                except urllib.error.HTTPError as e:
                    print(f"ERR {cid}: {_diagnose_http_error(e)}", flush=True); n_skip += 1; continue
                except Exception as e:
                    print(f"ERR {cid}: {type(e).__name__}: {e}", flush=True); n_skip += 1; continue

                # pooled span: final assistant turn, or from first evidence-bearing message
                #
                # 2026-09-14 (S10). Every apply-template call below renders a PREFIX of the
                # episode (msgs[:j] or msgs[:-1]) to locate a token boundary. Whenever the
                # dropped tail leaves an assistant message with tool_calls as the new LAST
                # message in that prefix -- which happens on essentially every tool-calling
                # episode, since the raw transcript's actual last message is normally the
                # tool result that resolves the model's final tool call, so msgs[:-1] ends
                # on that call's own assistant turn -- some llama-server builds 400 this
                # request outright: a request-validation guard in llama.cpp's server
                # (tools/server/server-common.cpp, gated by --prefill-assistant, ON by
                # default) rejects any request whose messages[] ends in an assistant message
                # carrying tool_calls ("Cannot continue an assistant message that contains
                # tool calls."), before the request ever reaches the model's chat template.
                # This is NOT a per-model chat-template incompatibility -- it is keyed only
                # on the shape of the LAST message in the request and fires identically for
                # every model, and only once the serving llama-server binary is built from a
                # commit that has this validation (confirmed: the exact same messages, same
                # GGUF, same --jinja default template replay clean against an older
                # llama-server build with no such check; a fresh clone-and-build from current
                # HEAD reproduces the 400 verbatim, including this error text). This call
                # previously sat OUTSIDE the try/except above, so hitting it crashed the
                # whole run and discarded every episode already captured in this process
                # (manifest.tsv is only written once, at the very end). Catch it here, keyed
                # on the server's own rejection text rather than on any model name, and skip
                # just this one episode with an actionable message instead of losing the run.
                # A no-op for every server build without this guard (all captures before
                # today), so behaviour for those trees is unchanged byte-for-byte.
                try:
                    pool_start = None
                    if a.pool_from_discovery:
                        for j, m in enumerate(msgs):
                            if "march-close-pack" in m["content"] or "warm cache" in m["content"]:
                                head = tpl(a.port, msgs[:j])
                                pool_start = len(post(a.port, "/tokenize",
                                                      {"content": head, "add_special": False,
                                                       "parse_special": True})["tokens"])
                                break
                    if pool_start is None:
                        head = tpl(a.port, msgs[:-1])
                        pool_start = len(post(a.port, "/tokenize",
                                              {"content": head, "add_special": False,
                                               "parse_special": True})["tokens"])
                except urllib.error.HTTPError as e:
                    print(f"ERR {cid}: {_diagnose_http_error(e)}", flush=True)
                    n_skip += 1; continue

                tf = os.path.join(a.out_dir, cid + ".txt")
                open(tf, "w").write("\n".join(map(str, toks)))
                json.dump({"cid": cid, "arm": arm, "tool_arm": tool_arm, "episode": i,
                           "model": log.eval.model, "eval_file": os.path.basename(p),
                           "n_messages": len(msgs), "n_tokens": len(toks),
                           "pool_start": pool_start,
                           "pool_mode": "discovery" if a.pool_from_discovery else "final_turn",
                           "scores": {k: (v.value if not isinstance(v.value, dict) else v.value)
                                      for k, v in (s.scores or {}).items()}},
                          open(os.path.join(a.out_dir, cid + ".meta.json"), "w"), indent=1,
                          default=str)
                man.append(f"{tf}\t{os.path.join(a.out_dir,'acts',cid)}\t{pool_start}\t{len(toks)}")
                print(f"{cid}: msgs={len(msgs)} toks={len(toks)} pool_start={pool_start}", flush=True)

    with open(os.path.join(a.out_dir, "manifest.tsv"), "w") as fh:
        fh.write("\n".join(man) + "\n")
    print(f"wrote {len(man)} streams, skipped {n_skip} -> {a.out_dir}/manifest.tsv")


if __name__ == "__main__":
    main()
