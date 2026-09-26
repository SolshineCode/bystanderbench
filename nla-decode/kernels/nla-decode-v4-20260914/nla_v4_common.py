# Shared reconstruction logic for NLA decode v4.
#
# This module is the SINGLE SOURCE OF TRUTH for how a recruiter-pilot episode's
# final-stage context is rebuilt.  It is imported by build_prefixes.py and
# verify_prefixes.py locally, and its two functions are inlined VERBATIM into
# script.py (Kaggle) and nla_decode_v4.ipynb (Colab), which have no way to
# import a sibling file.  If you change anything here, change it there too.
#
# ---------------------------------------------------------------------------
# WHY RECONSTRUCTION IS POSSIBLE AT ALL
#
# recruiter-trial/kernel_template.py::process_trial builds a single mutable
# `messages` list:
#
#     messages = [user(build_input(rec))]
#     for attempt in 0..MAX_ATTEMPTS-1:
#         used_ctx = deepcopy(messages)           # post-compaction snapshot
#         comp = generate_reply(messages, ...)
#         messages.append(assistant(comp))
#         stages.append({context_messages: used_ctx, response: comp, ...})
#         ... if the attempt failed and budget remains:
#         messages.append(user(error_feedback + beat_k))
#
# and then writes `messages` whole into transcripts.jsonl, while stripping
# `context_messages` out of the per-stage records (kernel_template.py:399).
#
# Because nothing else ever touches `messages`, the list is exactly
#
#     [u0, a1, u1, a2, u2, a3, u3, a4]
#
# so stage k's context is messages[:2k-1] and the FINAL stage's context is
# messages[:-1], with messages[-1]["content"] the final response.  There is no
# need to re-derive the error-feedback text or the recruiter beats from the
# BEATS/CONTROLS banks: the fully-formatted user turns are already in the list.
#
# The one thing that could break this is compaction.  generate_reply() does
# `messages[:] = [messages[0], messages[-1]]` in place when the context would
# overflow, which would permanently destroy the middle of the list.  Every
# stage of all 24 episodes has compacted=False, and assert_uncompacted() below
# refuses to proceed if that ever stops being true.
#
# The reconstruction is then CHECKED, not assumed: capture_stage() recorded
# pool_start / pool_end / n_tokens per stage into stage_acts/<sid>.json, and
# render_stage() reproduces the identical tokenisation so those integers can be
# compared exactly.
# ---------------------------------------------------------------------------

CTX = 16384          # run_meta.json["ctx"] for recruiter-gemma3-12b-20260904
PILOT_TOKENIZER = "unsloth/gemma-3-12b-it-bnb-4bit"   # run_meta.json["model_id"]


def final_stage_context(row):
    """(prefix_messages, response) for the final stage of one transcript row."""
    assert_uncompacted(row)
    ms = row["messages"]
    return ms[:-1], ms[-1]["content"]


def assert_uncompacted(row):
    """Refuse to reconstruct anything from a transcript that was compacted.

    Compaction rewrote `messages` in place, so the stored list would no longer
    be a superset of the per-stage contexts and messages[:2k-1] would be wrong
    for every stage.  Fail loudly rather than emit a plausible-looking prefix.
    """
    ms, stages = row["messages"], row["stages"]
    sid = row.get("sid", "?")
    bad = [s["attempt"] for s in stages if s.get("compacted")]
    if bad:
        raise SystemExit(
            f"ABORT {sid}: stages {bad} were compacted. generate_reply() rewrote "
            "`messages` in place, so transcripts.jsonl no longer contains the "
            "contexts the model actually saw and this reconstruction is invalid.")
    if len(ms) != 2 * len(stages):
        raise SystemExit(
            f"ABORT {sid}: len(messages)={len(ms)} != 2*n_stages={2*len(stages)}; "
            "the message list is not the plain user/assistant alternation this "
            "reconstruction assumes.")
    for i, m in enumerate(ms):
        want = "user" if i % 2 == 0 else "assistant"
        if m["role"] != want:
            raise SystemExit(f"ABORT {sid}: messages[{i}] role={m['role']!r}, expected {want!r}.")
    if ms[-1]["content"] != stages[-1]["response"]:
        raise SystemExit(
            f"ABORT {sid}: messages[-1] does not match stages[-1]['response']; "
            "the final assistant turn is not the captured final response.")


def stage_context(prefix_messages, response, attempt, n_stages):
    """Context + response for stage `attempt` (1-based), from the FINAL prefix.

    Stage k's context is a strict prefix of the final stage's context, so the
    whole per-episode stage sequence is recoverable from prefix_messages alone
    and verify_prefixes.py needs no second data source.
    """
    if attempt == n_stages:
        return list(prefix_messages), response
    return prefix_messages[:2 * attempt - 1], prefix_messages[2 * attempt - 1]["content"]


def render_stage(tok, context_messages, response_text, ctx=CTX):
    """Byte-for-byte replica of kernel_template.py::capture_stage's tokenisation.

    Returns (prompt_ids, response_ids, all_ids, pool_start, pool_end).

    Two details matter and are easy to get wrong:
      * the response text is taken as the SUFFIX of the rendered full chat, not
        as response_text itself, so it carries the closing <end_of_turn>\n; and
      * prompt and response are tokenised SEPARATELY and concatenated, which is
        not always the same as tokenising the concatenated text.
    """
    def chat_text(messages, gen_prompt):
        return tok.apply_chat_template(messages, add_generation_prompt=gen_prompt,
                                       tokenize=False)

    def toks_of(text):
        return tok(text, add_special_tokens=False).input_ids

    prompt_txt = chat_text(context_messages, True)
    full_txt = chat_text(context_messages + [{"role": "assistant", "content": response_text}],
                         False)
    resp_txt = full_txt[len(prompt_txt):] if full_txt.startswith(prompt_txt) \
        else response_text + (tok.eos_token or "")
    ptoks, rtoks = toks_of(prompt_txt), toks_of(resp_txt)
    toks = (ptoks + rtoks)[:ctx]
    return ptoks, rtoks, toks, len(ptoks), len(toks)
