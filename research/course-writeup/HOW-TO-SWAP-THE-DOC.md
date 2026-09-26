# Swapping the shared Doc, 2026-09-22

The rebuilt file is `research/course-writeup/BlueDot-BystanderBench-short-2026-09-22.docx`
(620 KB, 5 figures embedded, ~4,300 words). It carries all six of Caleb's decisions from the
2026-09-22 interview and every number re-derived from `cells_2026-09-21_nite.csv` plus §F210.

## Why I did not upload it

Two dead ends, both checked rather than assumed:
- The Drive connector's `create_file` takes base64. The file is 826 KB base64, which does not fit
  in the working context, and `update_file` writes metadata only, never content.
- Drive's "Manage versions" needs an OS file-picker dialog, which browser automation cannot
  drive. Typing 4,300 words into the Docs canvas was the other option and typing into Docs had
  already failed twice earlier in the session.

Leaving the Doc stale is recoverable. Leaving it half-overwritten is not, and it is the only
publicly reachable artifact this project has.

## The swap, which keeps the same link (about 30 seconds)

The link classmates have is the file ID `1wdrk6igKBt1AMABlYw9QVvUql2RDSiK3`. Keep it.

1. Open Drive and find `BlueDot-BystanderBench-short-2026-09-15.docx`.
2. Right-click it, then **Manage versions**, then **Upload new version**.
3. Pick `BlueDot-BystanderBench-short-2026-09-22.docx` from this repo.

That keeps the file ID, keeps the URL, keeps the "anyone with the link can comment" sharing, and
keeps the old version retrievable in the version list. Do NOT upload it as a new file; that mints
a new link and the shared one goes on serving the pre-09-15 draft.

Rename the file afterwards if you want the date in the title to match.

## What changes for a reader who already saw the old one

- The result they may have quoted, **58.3%**, is gone. The cell is 167/376 = 44.4%, and the
  significance moved from p = 0.0026 to p = 2.2e-8.
- "Six models, both conditions, nothing significant yet" becomes eighteen models with three that
  move.
- The "Runs in flight" section is gone; those runs finished a week ago.
- There is a new probe section, and it ends on a pre-registered causal null (§F210).

## Nothing is lost

Checked 2026-09-22 06:33: the Doc has **no classmate comments, replies or edits**. Sharing is
`anyone` at role commenter, Caleb is the only writer, and it has not been modified since
2026-09-15 21:07 UTC. The two threads in it are Caleb's own resolved suggestions from Sep 15.
Caleb confirmed the link was shared with the cohort, so the zero engagement is real rather than a
distribution failure.

## 2026-09-24 swap (done by Claude via Claude in Chrome, on Caleb's explicit "Do 1")

Uploaded `overhaul-2026-09-24/BlueDot-BystanderBench-2026-09-24.docx` as a new version of file ID
`1wdrk6igKBt1AMABlYw9QVvUql2RDSiK3` (Drive, Manage versions, Upload new version). Same link, same
sharing; the 09-22 version is kept as Version 4 in the version list. How the file picker was handled:
a page script intercepted `HTMLInputElement.click`/`showPicker` for file inputs so Drive's dynamically
created input stayed in the DOM without opening the native dialog, the extension's file_upload tool
set the file on it, and the original methods were restored afterwards. Verified with the Drive API:
same file ID, size 1,200,402 bytes, content starts with the new summary.

## 2026-09-25 swap

Same method, on Caleb's instruction ("Make sure you update the google docs we have shared link to our
classmates"). Uploaded `overhaul-2026-09-24/BlueDot-BystanderBench-2026-09-25.docx` as the new current
version; the 09-24 file is kept as version 5. Verified: same file ID, size 1,068,389 bytes matching the
local file, content starts with the new opening. Research-log entry for 2026-09-25 added the same session
through Chrome (typed at the end of the Doc) and read back through the Drive API.

## 2026-09-25 late swap (version 7)

After the third-quarter shortening, echo/kicker fixes, new closing and six agy flow edits. Same method.
Verified: same file ID, 1,067,666 bytes matching the local docx, new opening in the Drive snippet.
