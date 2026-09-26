#!/bin/bash
# §F211 mechanism check: does the patched llama.cpp ablate/clamp land where and as much as claimed?
# Runs two real nex agent-arm transcripts through extract_resid, linked against ~/llama.cpp-ablate.
set -uo pipefail
BASE=/home/darkstar/bluedot-unit2-impossiblebench; cd "$BASE"
GGUF=/home/darkstar/gguf-downloads/nex-n2.5-mini/Nex-N2.5-mini-Q4_K_M.gguf
OUT=research/f211/mech_f215; mkdir -p "$OUT"
SRC=bystander/acts_nex_agentarm.predecision/manifest.tsv
export LD_LIBRARY_PATH=/home/darkstar/llama.cpp-ablate/build/bin
ldd concealment-probe/tools/extract_resid | grep -q "llama.cpp-ablate/build/bin/libllama.so" || { echo "NOT LINKED TO PATCHED LIB"; exit 2; }
run(){ # name mode clamp cvecargs
  local name=$1 mode=$2 t=$3; shift 3
  mkdir -p "$OUT/$name"
  grep -E "nex-a__blatant_wrongdoing_agents_with_tool_native_tools_ep1(0)?\.txt" "$SRC" \
    | awk -F'\t' -v o="$BASE/$OUT/$name" '{n=split($2,p,"/"); print $1"\t"o"/"p[n]"\t"$3"\t"$4}' > "$OUT/$name/manifest.tsv"
  env ${mode:+LLAMA_CVEC_MODE=$mode} ${t:+LLAMA_CVEC_CLAMP=$t} RESID_MANIFEST="$OUT/$name/manifest.tsv" \
    RESID_LAYERS=4,8,16,24,30,34,37,39 CUDA_VISIBLE_DEVICES=0 \
    concealment-probe/tools/extract_resid -m "$GGUF" -c 32768 -b 1024 --cache-type-k q8_0 --cache-type-v q8_0 \
    --flash-attn on "$@" > "$OUT/$name/extract.log" 2>&1
  echo "$name rc=$? bins=$(ls $OUT/$name/*.bin 2>/dev/null | wc -l) mode_line=$(grep -o 'CVEC_MODE=[a-z]* CVEC_CLAMP=[-0-9.]*' $OUT/$name/extract.log | head -1)"
}
run plain "" ""
run abl_probe ablate "" --control-vector-scaled bystander/cvec/abl_probe_L1-39.gguf:1.0 --control-vector-layer-range 1 39
run abl_probe_L37 ablate "" --control-vector-scaled bystander/cvec/unit_probe_L37.gguf:1.0 --control-vector-layer-range 37 37
run abl_random_L37 ablate "" --control-vector-scaled bystander/cvec/unit_random_L37.gguf:1.0 --control-vector-layer-range 37 37
