# Packet 1: what does this pattern respond to?

About 20 minutes. Stop and come back whenever you need to.

## The idea

Inside an AI model there are thousands of little parts. Each one switches on for some kinds
of text and stays off for others. Some match something a person can name, like "quoted
speech" or "measurements". Plenty match nothing you could describe.

You're looking at seven of them, A to G.

## What you do

For each one, you get 12 short pieces of text. These are the places where that part
switched on hardest. The exact word it reacted to is marked `>>>like this<<<`.

Read the 12 pieces. Look at the marked word, and at the text around it. Then write two
things in the CSV:

1. **One sentence.** What does this one seem to react to?
2. **A number from 1 to 5.** 1 means you're guessing. 5 means the pattern is obvious.

Then go to the next one. Seven in total, in order.

## Both kinds of answer are equally useful

If you see a pattern, describe it.

If you don't, write **"no pattern I can see"** and put 1 for confidence.

Don't stretch to find something that isn't there, and don't hold back something you can
see. Either way, just say what you found.

## Odd things you'll notice

**Strange tags** like `<bos>` or `<start_of_turn>`, sometimes chopped off. These are
internal markers, not something a person wrote. Ignore them, unless a part seems to react to
them specifically, in which case say so.

**The same source text turning up in more than one place.** All the pieces are drawn from
one pool, so this happens. It doesn't mean two parts are related.

## Heads up on content

Some pieces contain sexually explicit material, and some describe coercion and abuse. It's
real text the model was tested on, not anything we wrote.

Skip anything you don't want to read. Note which ones you skipped at the bottom of the CSV
and judge that part on the rest. To skip a whole part, write "skipped" and leave the
confidence blank. No explanation needed.
