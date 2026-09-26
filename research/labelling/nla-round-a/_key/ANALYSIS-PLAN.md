# Round A analysis plan — written BEFORE any rater sees the packet

Pre-registered on 2026-09-13, in the spirit of §F104: the prediction and the kill condition
go on the record first, so a disappointing result cannot be re-described afterwards as the
one I expected.

## What is being tested

§F152 claims the NLA decoder's positive control works. That claim currently rests on me
reading four decodes and judging that they matched their sources. CLAUDE.md's
interpretability rule 3 says an interpretation you reached yourself is a single-agent
autolabel until independently checked. This is the check.

## Design

Four decodes (D1-D4), eight candidate source texts (S1-S8), one choice each. Two candidates
are the real sources; six are decoys, balanced four code / four prose because the decodes
plainly give away the domain. **Score against within-domain chance, 1/4, not 1/8.**

`decoy_code_solve` deliberately shares `def solve(` with the real code source, so the code
items cannot be answered from that one token alone.

## Per-item prediction, made in advance

Measured word overlap between each decode and its own correct source:

| item | decode | content words shared with its answer | prediction |
|---|---|---|---|
| D1 | `val_weather_mid` | forecast, heavy, rain, strong, winds | **should be got**, and easily |
| D3 | `val_code_cheat_flavor_last` | return, solve, test | **should be got**, needs discriminating from `decoy_code_solve` |
| D4 | `val_weather_last` | forecast | **marginal** — one content word, but no other prose candidate mentions a forecast |
| D2 | `val_code_cheat_flavor_mid` | *(none)* | **expected at chance.** This decode names factorial, collatz and Haskell, none of which is in the source. The decoder got the domain and missed the content. |

So the honest expectation is **2 to 3 of 4**, not 4 of 4. D2 is a real per-vector failure of
the decoder, recorded here in advance so that a 3/4 result is not later spun as a clean pass.

## Decision rules

- **Confirms §F152's positive control:** D1 and D3 both correct. Under within-domain chance
  that is p = 1/16 = 0.0625 for those two alone, which is weak on its own, so the qualitative
  read matters: a rater who picks the right text *and* explains it by the quoted phrase is
  stronger evidence than the count.
- **Overturns it:** D1 wrong. D1 is the item where the decoder reproduced five content words
  of the source. If a person cannot match that decode to that text, my reading of all four
  decodes was wrong and §F152 needs a correction block, not a footnote.
- **Ambiguous, and treated as such:** anything else. Two raters at 2/4 with different items
  correct is not a positive result.

## Limits stated in advance

n = 4 items and a handful of raters. This can confirm that a decode is legible to someone
other than me; it cannot estimate how often the decoder is right in general. It says nothing
about the project vectors, whose decodes are the §F152 null.

The key is `round-a_KEY.csv` in this directory. It is never sent to a rater.
