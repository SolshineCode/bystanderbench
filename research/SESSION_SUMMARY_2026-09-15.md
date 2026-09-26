# Session summary — overnight 2026-09-14 → 2026-09-15 (deep-work continuation after the ~16:58 crash/reboot)

Brief carried over from the 09-13 plan: bulk existing cells, no new investigations; present funds
to RunPod mech-interp; no paid OpenRouter without a per-launch go-ahead (none launched); no
transformers `.generate()` on the M40s (none run). Push is blocked all night: the GNOME Login
keyring is locked at the GDM greeter after the reboot, so `gh` cannot read its token. Twelve commits
wait on `main` for a desktop login; nothing else is needed (memory note
`gh-push-blocked-after-reboot-keyring`).

## Landed (committed, in order; all pushed to HF with MD5 read-back, none pushed to GitHub yet)

1. **§F172 gemma-3-27b-it on a rented A40, prompted CLI mode.** Floor 6/6 (table 7/7 with the
   smoke) while failing the cover task 0/6; incident-1 ceiling alerted 6/12, discovered_content
   4/12, cover 2/12 → REFUSED on competence, exactly gemma-3-12b's number (§F148). All six
   escalations read by hand: shell errors, a missing fixture, the model's own `FINAL:` loop; none
   name the fabrication; two of the six had already read the incriminating file. The
   pre-registered gate stopped ceilings 2 and 3 after ceiling 1 (`w11_competence_gate.sh`), saving
   ~1.7 h of pod time. 18 episodes captured, extracted ON THE POD (see provenance), 16 layers,
   `bluedot-unit2-bystander-gemma3-27b-pod-2026-09-15` (77 files, 6/6 read-back).
2. **§F173 NLA v4 duplicated on the A40 in bf16.** 78 decodes, controls pass on both machines;
   vector norms agree to a median 5e-4 relative; decoded text agrees for a median 227 characters
   then diverges under greedy decoding; domain profile agrees 64/78. Rule: NLA decodes are cited
   by opening sentences and domain, never exact strings. Dated correction the same night: the
   Round B packet (built 09-14) uses full decodes, which is fine for raters; the rule is for claims.
   `bluedot-unit2-nla-decode-runpod-2026-09-15` (4/4 read-back). Colab duplicate no longer needed.
3. **§F174 qwen3.8:27b row 10 at n=100.** The owed `conflicting` split: 0/25 concealed, 13
   `disclosed` (hand-read, all `visible_prose`, none docstring copies), 12 `failed_silent`.
   Impossible total 0/50 concealed, 18/50 disclosed; competence 30/50 unchanged (below floor).
   100/100 bins; layer 64 silently dropped (§F156 third recurrence; 11-layer delivered set
   recorded). `bluedot-unit2-concealment-probe-qwen38-27b` (310 files, 8/8 read-back). Row 10
   written via a new `build_rates.py --allow-drift MODEL` (refuses unnamed drift, verified).
   Fig 4 rebuilt (only that point moved).
4. **§F175 lightning thinking-OFF incident 1 at n=25** (0/25 alerted, 0/22 conditional, cover
   25/25, floor 6/6) and **§F176 qwen3.5-27b native incident 1 at n=25** (0/25, 0/16 conditional,
   cover 25/25, floor 16/16 in the table). Both launched through condition-gated launchers: the
   smoke episode's report.py key had to match the cell being topped up (`tools/native` without
   `+think`) or the launcher aborted. Trees `…-lightning-nothink-ext-2026-09-15` (52 files) and
   `…-qwen35-blatant-ext-2026-09-15` (37 files). Figures 1, 3, 6, 7 rebuilt and checked by eye.
5. **Cell table `cells_2026-09-15_after_w4c.csv`**: 89 cells, 10 refused; built by the new
   `bystander/make_cells_csv.sh` from a content-defined logdir set. The first rebuild tonight used
   a name pattern and silently dropped the eight `logs/orpaid-*` frontier dirs (78 cells against
   87); the script now reproduces the 09-14 table exactly plus the new cells. Smoke episodes pool
   with their key (they always did; METHODOLOGY-v1.1 addendum, §F172/§F175 table addenda).
6. **Tooling with negative-case checks:** `check_layers.py` accepts `--expect` in either position
   (the `dir --expect L` form was treating the flag as a directory and exiting 1 with "no .bin
   files", which §F169 had called a glob quirk); `bystander/push_acts_tree.py` (identity guard,
   folder upload, sampled MD5 read-back); `bystander/runpod/` and `bystander/launchers/` file the
   scripts the ledger cites.
7. **Course write-up** (long, short, HF appendix now 28 datasets, TODO) synced through §F176;
   figures.md and the figure builder repointed to the new table.

## Corrections made tonight (all dated, additive)

- The local gemma-3-27b GGUF is ggml-org's build, not bartowski's, and not byte-identical (256 B
  size delta hidden by rounding): the "extract locally on the same file" plan was wrong on both
  counts, so extraction ran on the pod against the generating file (`extract_resid` relinked
  against the pod's newer llama.cpp: `-lllama-common` + `libllama-common-base.a`). The gemma-4-31b
  bins from 09-14 were re-checked: local file == hub file, repo unchanged since 07-17, same-file.
  Audit record `research/audits/2026-09-15-w11-gguf-provenance.md`.
- §F173's "Round B items use the first two sentences" was false (full decodes); corrected inline.
- The "glob quirk" in §F169 was the argument-order bug above; named in §F172, fixed.

## Spend

- RunPod pod `00jz5m3ou6z00i` (A40 SECURE, CA-MTL-1): 00:36–02:27 PDT, ≈$0.93 estimated
  (1.86 h × $0.49 + 80 GB disk); terminated via the API and verified absent. Cumulative RunPod
  ≈$1.95. **Caleb: read the actual charge and replace the estimate in §F172 and the spend log.**
- OpenRouter: $0 tonight (free tier exhausted at the 09-14 cap; paid chain stopped before spend,
  deferred to the grant extension).

## Not run, and why

- Free-tier top-ups (ling-vl, ling-sante, lightning-hosted, nemotron-super to n=12; ling-fin
  partial): daily cap resets 17:00 PDT; `w9_free_topup_chain_v2.sh` is the launcher.
- Plan item "probe refit on lightning / north-mini / gemma trees": moot, no second model has both
  alert and silent classes, so there is nothing to fit; nex remains the only probe model.
- gemma-4-31b cells to n=24: pod-only model, out of tonight's pod scope.

## In flight at wind-down

Nothing. Both GPU reservations released (c898bce4 at 04:59, f580cb51 at 06:07), no llama-server,
no sandboxes, pod down. Cron: 08:57 wind-down timer (re-created after the reboot wiped it).

## Owed to the day (priority order)

1. Log into the desktop once → keyring unlocks → `git push` (12 commits). No key or re-login needed.
2. Grant extension email: `messages/2026-09-15-bluedot-grant-extension-request.md` is a DRAFT;
   check the labeller sentence and the amount, then send on the thread.
3. RunPod billing read (above). HF listing check before release (28 datasets in the appendix;
   `bluedot-unit2-bystander-acts-*` are listed in MANIFEST's table form, not the bullet form).
4. Free-tier chain after 17:00. Opus benign control ($2.67) is still a Caleb decision.
5. Make the 28 datasets and the repo public at release time (every card has its dated notes).

## Wind-down (timer 08:57)

Timer fired 08:57:17. Verified: working tree clean apart from the standing local-only artifacts;
`main` 12 commits ahead of `origin/main`; keyring still locked (`busctl … Locked = true`), so no
push, and a background watcher keeps polling every 5 minutes and pushes the moment it unlocks; no
gpusched reservation held, both GPUs at 0 MiB, no llama-server, no sandbox, pod absent from the
RunPod list. Every result landed tonight (§F172–§F176) has its ledger entry, HF dataset with MD5
read-back, MANIFEST row and appendix row. No GPU or paid work started after 06:07.

**Final state 09:00:** ledger through §F176; cell table `cells_2026-09-15_after_w4c.csv`; 28
project datasets on the hub, all private; nothing running; owed-to-the-day list above stands.
