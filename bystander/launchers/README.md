# Local cell launchers (verbatim from the overnight session job dirs)

Filed because the ledger cites them by name (§F169 `w4_lightning_ext.sh`, §F170 `w8_nex_inc23_gpu0.sh`,
§F174 `w5b_qwen38_conflicting_score.sh` / `p1_qwen38_conflicting_extract_v2.sh`, §F175
`w4b_lightning_nothink_ext.sh`, §F176 `w4c_qwen35_ext.sh`). Not parameterised; each is the record of
what ran. Absolute paths point at the darkstar box. Pattern shared by all: `tools/require_reservation.sh
<tag> <gpu>` first, llama-server on one GPU with the exact serving line of the cell being extended,
smoke one episode and read it, then the episodes into a new `-ext` logdir (report.py pools by key,
originals untouched), capture, extract, `check_layers.py --expect`, pooled report, `gpusched release`.
The 09-15 launchers add a condition gate: the smoke's report.py key must match the cell being topped
up (`mode=tools/native` vs `+think` is decided per log by the majority rule, §F161), else abort.
