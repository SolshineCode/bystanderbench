import re, sys
src = open(sys.argv[1]).read()
out = []
for ln in src.splitlines():
    if ln.startswith('[[FIG') or re.match(r'^Figure \d+\.', ln) or not ln.strip():
        continue
    if ln.startswith('## Appendix'):
        break
    if ln.startswith('#'):
        out.append(ln.lstrip('#').strip() + '.'); continue
    ln = re.sub(r'^\d+\.\s+', lambda m: 'Finding ' + m.group(0).strip().rstrip('.') + ': ', ln)
    ln = re.sub(r'^- ', '', ln)
    out.append(ln)
t = '\n\n'.join(out)
R = [
 (r'\[([^\]]+)\]\((?:https?://)[^)]+\)', r'\1'),   # markdown links -> their text
 (r'\s*\[\d+(?:\.\d+)?, \d+(?:\.\d+)?\]', ''),                      # drop Wilson CIs
 (r'`([^`]*)`', r'\1'), (r'\*\*?([^*]+)\*\*?', r'\1'),
 (r'p = (\d(?:\.\d+)?)e-(\d+)', r'p equals \1 times ten to the minus \2'),
 (r'p < ', 'p below '), (r'p = ', 'p equals '), (r'≥', 'at least'), (r'>=', 'at least'),
 (r'rho -0\.19', 'rho of minus 0.19'), (r'-0\.19', 'minus 0.19'),
 (r'\b(\d+)/(\d+)\b', r'\1 of \2'),
 (r'alert_oversight', 'alert oversight'),
 (r'gpt-5\.6-luna-pro', 'G P T 5.6 Luna Pro'), (r'gpt-5\.6-luna', 'G P T 5.6 Luna'),
 (r'gpt-5\.(\d)', r'G P T 5.\1'), (r'\bluna-pro\b', 'Luna Pro'),
 (r'nex-n2\.5-mini', 'Nex N 2.5 Mini'), (r'nemotron-3\.5-lightning', 'Nemotron 3.5 Lightning'),
 (r'qwen3\.5-27b', 'Qwen 3.5, 27 B'), (r'llama-3\.3-70b', 'Llama 3.3, 70 B'), (r'llama\.cpp', 'llama C P P'),
 (r'north-mini-code', 'North Mini Code'), (r'\bdots-3\b', 'Dots 3'), (r'\blaguna-s\b', 'Laguna S'),
 (r'\bAUC\b', 'A U C'), (r'\bLLM\b', 'L L M'), (r'\bMETR\b', 'Meter'), (r'OpenRouter', 'Open Router'),
 (r'\bBystanderBench\b', 'Bystander Bench'), (r'\bImpossibleBench\b', 'Impossible Bench'),
 (r'\(37\)', '37'), (r'\$500', '500 dollar'),
 (r'"', ''), (r'\s+', ' '),
]
for a, b in R:
    t = re.sub(a, b, t) if a != r'\s+' else t
t = re.sub(r'[ \t]+', ' ', t)
open(sys.argv[2], 'w').write(t)
print(len(t.split()), 'words')
