import os, sys, glob
# Walk OWN ancestry first. The shell running this tool has the script name in its cmdline
# as ordinary heredoc text, so a name match without this exclusion always says "busy".
me = os.getpid(); anc = set(); p = me
for _ in range(25):
    try: st = open(f"/proc/{p}/stat").read().rsplit(")", 1)[1].split()
    except Exception: break
    anc.add(p); p = int(st[1])
    if p <= 1: break
busy = []
for d in glob.glob("/proc/[0-9]*"):
    pid = int(d.split("/")[-1])
    if pid in anc: continue
    try:
        exe = os.path.basename(os.readlink(d + "/exe"))
        cmd = open(d + "/cmdline", "rb").read().decode(errors="replace").split("\x00")
    except Exception: continue
    if exe in ("bash", "sh", "dash") and any("run_pilot_local" in c or "run_smoke_local" in c
                                             for c in cmd if c):
        busy.append((pid, " ".join(c for c in cmd if c)[:80]))
if busy:
    print("REFUSING, target script is executing:", busy); sys.exit(1)
print("guard: clear (excluded own ancestry:", sorted(anc), ")")

EDITS = [
  ("bystander/run_pilot_local.sh",
   '    REASONING_ARGS="--reasoning off"\nfi',
   '''    REASONING_ARGS="--reasoning off"
fi
# THINKING BUDGET (2026-09-12, S-F123). `--reasoning off` does NOT stop a hybrid model from
# thinking; it only controls whether the tags are parsed out. On the ImpossibleBench coding
# task nex-n2.5-mini ran a single generation to 27,153 tokens under `--reasoning off` and
# would have filled the whole 32K window. `--reasoning-budget 0` ends thinking immediately
# and took the same episode from hours to about three minutes. Left UNSET by default so every
# bystander result before this date reproduces exactly; set REASONING_BUDGET=0 for any new run
# on a hybrid model, and expect a bare `</think>` prefix in the output (which
# screen_behavioral.visible_part's LOOSE_THINK already strips).
[[ -n "${REASONING_BUDGET:-}" ]] && REASONING_ARGS="$REASONING_ARGS --reasoning-budget ${REASONING_BUDGET}"'''),
  ("bystander/run_smoke_local.sh",
   '-ngl 999 -c "$CTX" -np 1 --no-webui --jinja --reasoning off \\',
   '-ngl 999 -c "$CTX" -np 1 --no-webui --jinja --reasoning off \\\n'
   '    ${REASONING_BUDGET:+--reasoning-budget "$REASONING_BUDGET"} \\'),
]
for path, old, new in EDITS:
    s = open(path).read()
    assert old in s, f"anchor missing in {path}"
    open(path, "w").write(s.replace(old, new, 1))
    print("patched", path)
