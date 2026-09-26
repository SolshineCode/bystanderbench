# Audiobook build

Turns a write-up into an MP3 with Piper, entirely offline and off the GPUs.

```bash
python3 -m venv /tmp/ttsenv && /tmp/ttsenv/bin/pip install piper-tts
curl -sL -O https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
curl -sL -O https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

python3 tools/audiobook/mdspeak.py research/drafts/writeup-unit4-2026-09-12.md > speak.txt
/tmp/ttsenv/bin/python tools/audiobook/tts.py en_US-lessac-medium.onnx speak.txt out.wav
ffmpeg -i out.wav -codec:a libmp3lame -b:a 96k -ar 22050 out.mp3
```

`mdspeak.py` exists because this write-up is unlistenable read literally. "9/48" comes out
as "nine forty-eighths", "§F122" as a glyph, and a markdown table as a run of pipes. It
rewrites the notation, reads tables as sentences, and expands the acronyms this project uses
constantly.

`piper -i file` only synthesizes the first line, which is why `tts.py` drives the Python API
per paragraph and writes its own 0.45s gaps. Without those the sections run together.

**Check the output, don't trust the exit code.** `ffprobe` for a duration that matches the
word count at roughly 160 wpm, and `volumedetect` on two or three offsets to confirm there is
real audio rather than silence:

```bash
ffmpeg -hide_banner -nostats -ss 600 -t 15 -i out.mp3 -af volumedetect -f null - 2>&1 | grep volume
```
