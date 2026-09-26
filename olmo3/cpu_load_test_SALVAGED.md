# olmo3 cpu_load_test — salvaged content, 2026-09-07

The original olmo3/cpu_load_test.log was 1.9 GB / 985,338,996 lines, of which only
~22 lines were unique: an interactive llama-cli session that loaded the model, answered
one prompt, then sat at an idle '>' prompt writing spinner frames and ANSI escapes to
disk until something stopped it. Deleted 2026-09-07 (Caleb's go-ahead) after extracting
everything below. Nothing else was in it.

## What it actually recorded (a SUCCESSFUL run, not a failure)

    > Say OK.
    Loading model... |^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H ^H
    [ Prompt: 6.9 t/s | Generation: 6.5 t/s ]
    build      : b9879-72874f559
    ftype      : Q4_K - Medium
    modalities : text
    model      : /home/darkstar/gguf-downloads/olmo-3-7b-instruct/Olmo-3-7B-Instruct-Q4_K_M.gguf
    |^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H/^H-^H\^H|^H ^HOK.

## Correction to olmo3/serve_olmo3.sh

serve_olmo3.sh line 8 cites this file as verification that the bundled chat template
aborts this build's minja. **The file contains no abort, error, or assertion of any
kind** — a grep for error/abort/assert/exception/fail/minja/terminate across all 985M
lines returned zero hits. It shows a clean load and a successful generation. The
template-abort finding may well be real, but this file is not evidence for it, and the
citation should point at whatever log actually captured the abort.
