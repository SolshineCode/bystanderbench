#!/usr/bin/env python3
"""Speakable text -> one WAV. Paragraph by paragraph, with a real pause between them,
because a 2,900-word block read with no breaks is exhausting to listen to."""
import sys, wave
from piper import PiperVoice
from piper.config import SynthesisConfig

voice = PiperVoice.load(sys.argv[1])
text = open(sys.argv[2]).read()
paras = [p.strip() for p in text.split("\n") if p.strip()]
cfg = SynthesisConfig(length_scale=1.0)

with wave.open(sys.argv[3], "wb") as w:
    first = True
    for i, p in enumerate(paras):
        voice.synthesize_wav(p, w, syn_config=cfg, set_wav_format=first)
        first = False
        # A beat between paragraphs. Without it the sections run together.
        w.writeframes(b"\x00\x00" * int(voice.config.sample_rate * 0.45))
        if i % 10 == 0:
            print(f"  {i}/{len(paras)}", flush=True)
print(f"done: {len(paras)} paragraphs")
