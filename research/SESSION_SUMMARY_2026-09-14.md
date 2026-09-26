# Session summary — overnight 2026-09-13 23:20 → 2026-09-14 (GPU grant, 10h)

Brief: no new investigations; bulk volume, breadth and scale on what exists so the corpus
reaches reviewer-grade rigor; probes and NLA improve because the data got bigger; a scaling
read only if derivable from the bulked table. Every lane at once: free-tier OpenRouter, both
M40s, Kaggle, RunPod (≤$10), subagent swarm, Antigravity as cross-family reviewer.

## Landed (committed + pushed, in order)
- `cb55607` — **§F161** reporter provenance fix: locally served runs keyed by the GGUF the
  server itself recorded in every completion (`sample.output.model`), plus a thinking-condition
  key. Refused cells 32 → 8 at first pass. Antigravity (Gemini 3.1 Pro) review filed under
  `research/audits/`. New tooling: `scaling_read.py`, `decision_index.py`, NLA v4 kernel +
  Colab twin; before/after cell CSVs.
- `6244217` — **§F161 correction**: the reviewer was right and my rebuttal misread a scorer
  metric as a server flag; inline `<think>` runs are thinking-ON; flag is now local-only,
  per-log majority. Final: **78 cells, 9 refused** (5 no-channel arms, 3 competence, 1 correct
  new refusal). Lightning honestly split: thinking-OFF 0/12 (n=12), thinking-ON 0/20 (n=24).
  nex headline 11/53 → 16/83. qwen3.5-27b (~200 episodes) citeable, silent on every incident.
- `bb27f0b` — NLA v4 Kaggle results (78 decodes) committed.
- `e0ef0fb` — **§F162** NLA v4: controls behave (positive → content, random-direction negative
  → fluent generic text, so fluency is not evidence); project decodes collapse to template
  (22 distinct openings of 72); one nominal keyword hit in six, carried by the word
  "placeholder", reported as an observation not a result; **Round B** built, grep-verified,
  unsent. HF: `DarkStarDeleeuw/bluedot-unit2-nla-decode-kaggle-2026-09-14` (MD5 read-back 5/5),
  MANIFEST row added.

- `1f5d45d`/`845894b` — **§F163** gemma-4-31B-it on three incidents via RunPod ($1.02, pod
  verified terminated): floor 6/6, cover 12/12 ×3, alerted 0/12 ×3, discovered 1/12, 0/12, 0/12
  (S8 transcript read filed under `research/audits/`); capture guard for the llama-server
  `--prefill-assistant` version-skew 400; token tree 43/43 captured locally.
- `86b4898` — twelve completed eval logs force-added (free-tier floors/ceilings, pod cell).
- `9b2acb8` — **§F164** free-tier breadth: nano 3/6 (fail), ultra 6/6 → **0/8**, laguna-s 6/6 →
  **1/12**, laguna-xs 6/6 (ceiling capped), lfm 0/6 (fail), gemma-4 ×2 upstream 429, inkling ×2
  app-gated; daily cap reached 04:30.
- `060d3a9` — **§F165** qwen3.8:27b row 10: competence **30/50 = 60.0% [46.2, 72.4]**, below the
  0.75 floor — §F160's band resolved; oneoff 0/25 concealed (5 `disclosed`); `conflicting`
  aborted by my own server kill at 06:38 (owed); scored on a CPU-only server.
- Scaling read over the final 87-cell table (`research/audits/2026-09-14-scaling-read.md`):
  pooled Spearman n=34, ρ=−0.21, perm p=0.22; no family with ≥3 reportable sizes; MDE 57 pp at
  n=12 — a null, stated as one.

## Spend
RunPod pod `bkcnw1vglpmfzb` (A40, $0.50/hr) live from 23:59; balance $54.91 at start; hard
stop $8 (floor $44.91). Kaggle: one T4×2 kernel, 108 min. OpenRouter: `:free` only.

## In flight at 08:40 (carry into the day; reservations extended, nothing killed mid-episode)
- **W2** nex +24 on GPU 0 (reservation 94236759 → 10:32): batch j done 12/12 — the pooled
  incident-1 cell is now **n=108, 26/106 = 24.5%** with batch k (batch rates 8–58%, which is
  binomial noise at n=12, not a batch effect — corrected in §F166); batch k running since 08:24 (~09:15), then capture + 8-layer extraction
  (`acts_nex_pos_jk`), then **W2b** (queued): `pool_bounds.py` cut → truncated extraction →
  `probe_alert.py --predecision` refit → `research/canonical/probe_alert_predecision_v2.json`
  (n 98 → 122). Monitors armed; §F166 to write from the refit.
- **W7** gemma-4-31B extraction on GPU 1 (557d45c0 → 14:38): 18/43 bins at 07:43, ~3.6 min/ep,
  ETA ~09:15; then `check_layers --expect 4,8,16,24,32,40,48,56`, HF push (read-back), MANIFEST
  row, dated line under §F163, release.
- **W4** lightning +12 ×3: launcher ready (`w4_lightning_ext.sh`), did not fit — for the day.
- Free tier: cap resets 17:00 PDT; phase-2/3 launchers re-runnable unchanged (laguna-xs
  ceiling, gemma-4 floors, ten n=6→12 top-ups, incidents 2/3 for passers).
- Part 1 qwen3.8: `conflicting` re-run (~10 h) and residual extraction over
  `concealment-probe/data/qwen38/qwen38-27b/manifest.tsv` — for the day.
- Write-up number sync (#42): subagent diff in progress; applied at wind-down if it lands.

## Process notes
- Worktree guard: repo-local `.claude/settings.json` sets `bgIsolation: none` (excluded from
  git) because running jobs, untracked `logs/`, and gitignored capture trees make a worktree
  unusable here.
- Killed my own shell once (exit 144) with an inline `/proc` walk — the walker now lives in a
  file (`find_inspect.py`); memory updated.
- Colab lane not run: needs `HF_TOKEN` as a Colab secret set by Caleb.

## Wind-down (timer fired 08:57)
- **Reservations deliberately kept**, not released: `94236759` (GPU 0, → 10:32) covers W2
  batch k (5/12 at 08:57) → capture → extraction → W2b; `557d45c0` (GPU 1, → 14:38) covers W7
  (40/43 bins at 08:57, ~09:08). Releasing a reservation under a running job is the lapse the
  check-in rule exists to prevent; GPU 1's is released the moment W7 lands, GPU 0's is the
  day's to release after W2b. Nothing was killed mid-episode.
- Docker: one zombie found and removed — `run_eval_gpu.py --label part1-qwen38-conflicting`
  (PID 444625) had survived my 06:40 kill of its parent launcher and was retrying against the
  dead port; it and its sandbox (`lcb_conflict`, 08:00) are gone. Remaining container is W2's
  live batch-k sandbox. Kaggle: COMPLETE. RunPod: pods list empty, balance $53.86 — total
  spend **$1.05**.
- Commits this session: `cb55607`, `6244217`, `bb27f0b`, `e0ef0fb`, `1f5d45d`, `845894b`,
  `86b4898`, `9b2acb8`, `060d3a9`, `2234b01`, `4849d98`, `682874a`, `f59cf3a`, `5ebc2c9`, `27586bf` (+ this one).
  Ledger §F161–§F165. HF: `bluedot-unit2-nla-decode-kaggle-2026-09-14` (read back 5/5).

## Owed to the day (in priority order)
1. ~~W2b~~ DONE 10:27: **§F167** written (honest AUC 0.586 → 0.675, p 0.14 → 0.07/0.12, verdict unchanged); trees pushed as `bluedot-unit2-bystander-nex-pos-jk-2026-09-14` (read-back 4/4); `94236759` released — both cards empty at 10:30. Was: W2b output → §F167 (probe refit v2, n 98 → 122; `research/canonical/probe_alert_predecision_v2.json`); push `acts_nex_pos_jk` (+`.predecision`) to HF; MANIFEST rows; release `94236759`.
2. ~~W7~~ DONE 09:08: 43/43 bins (every bin 516,096 B = 8×3×5376×4), pushed as `bluedot-unit2-bystander-gemma4-31b-pod-2026-09-14` (read-back 3/3), MANIFEST row, §F163 follow-up, `557d45c0` released (`27586bf`). Fix `check_layers.py`'s glob ("no .bin files" on this tree).
3. W4 lightning +12 ×3 (`w4_lightning_ext.sh`, GPU 0 after W2b) — headline cell n 12 → 24.
4. Part 1 qwen3.8: `conflicting` re-run (~10 h) and residual extraction over `data/qwen38`.
5. Free tier after the 17:00 PDT reset: laguna-xs ceiling, gemma-4 floors, ten n=6→12 top-ups, incidents 2/3 for passers (phase-2/3 launchers unchanged).
6. Re-derive the three flagged p-values in the write-up from `report.py` (lines 145, 154, 195).
7. Round B: send when Caleb decides; Colab twin needs `HF_TOKEN` as a Colab secret (his action).

**Final state 10:30:** ledger through §F167; both GPU reservations released; pod down; Kaggle complete; tree clean. The day's list is items 3–7 above.
