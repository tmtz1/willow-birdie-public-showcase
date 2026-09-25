# Four AI assistants tried the same small code repair

**The short version:** GPT-5.6-SOL, GPT-6-SOL, GPT-6-Astra, and Claude Opus 5.5 all fixed the same problem in an offline test. All four passed the same 30 checks. GPT-6-SOL finished fastest *in these single runs*. That is not proof that it is the best assistant for other work.

## What were they trying to fix?

Imagine asking an assistant to post a reply. The sending program closes without an error. Did the reply actually get accepted? Not necessarily. Our small reply-helper program treated that clean exit as success, even if the program's confirmation was missing or wrong.

Each AI assistant received the same starting code and instructions: make the helper require a clear, valid confirmation before saying “sent.” Keep the existing safeguards so a failed attempt does not automatically send a duplicate. This code came from a local prototype, **not a confirmed copy of a live service**.

We asked each assistant to write checks that caught the bug, then gave it the failing results and asked for a fix. After the fix, our own test runner—not the assistant's word—checked the work. Each assistant then reviewed the results. None was allowed to send a real message.

## How did the four do?

- **GPT-5.6-SOL:** Fixed the problem and passed all 30 shared checks. Its own 10 checks also passed after the fix. Recorded run time: **about 5.4 minutes**.
- **GPT-6-SOL:** Same shared result, **30/30**. Its own 8 checks passed. Recorded run time: **about 2.6 minutes**—fastest here.
- **GPT-6-Astra:** Same shared result, **30/30**. Its own 10 checks passed. Recorded run time: **about 3.9 minutes**.
- **Claude Opus 5.5:** Same shared result, **30/30**. Its own 31 checks passed. Recorded run time: **about 4.5 minutes**.

All four assistants' checks *first failed on the original broken code*, then passed on their fixes. The original code failed 19 of the 30 shared checks; the four repaired versions passed them all.

**What stands out?** On the common checks, this was a four-way tie for correctness. The only clear difference measured here was how long these particular runs took: GPT-6-SOL, then Astra, then Opus, then GPT-5.6-SOL. Claude wrote more of its own checks, but more checks do not automatically mean a better fix: the assistants chose different cases, and all four faced the same independent 30-check exam. GPT-6-SOL also used fewer reported main-model tokens than the other OpenAI/Codex runs; Claude's subscription reports cached work differently, so its token figures are not a clean head-to-head efficiency score.

## What this does—and does not—show

This is **one code repair, once per assistant**, not a broad test of intelligence or an average across many tasks. Time includes program startup, waiting on providers, and small extra requests made to label each session. The models used different access tools and may have faced different provider load, so the order could change on another day. No verified price comparison is available.

The four extra process checks started a *stand-in Python program* to imitate a sender. They did **not** talk to the real Buzz sender or relay. Passing these offline checks does not mean a patch is installed, approved, or safe to deploy. In the Opus run, its structured review said “ship” while its explanation said “approved for merge only”; neither is permission for a live rollout.

## For readers who want to inspect the evidence

The same [starting code](baseline/reply.py) and [shared tests](tests/) are here, alongside each assistant's [repaired code and self-written tests](candidates/). The public files replace private paths and channel identifiers with harmless examples. The original SOL comparison used the same 26 prewritten acceptance checks and later added the same four process checks. Astra and Opus were run against that frozen 26-check suite and the same four process checks, then their public, sanitized versions were re-run alongside both SOL versions on all 30.

Details for reproducibility:

- Models and routes: `gpt-5.6-sol`, `gpt-6-sol`, and `gpt-6-astra` through `openai-codex`; `claude-opus-5-5` through a first-party Claude Code Pro subscription. Exact prompts and private provider receipts are not published.
- Same three-stage sequence for each: write regression tests and see them fail on the original, write the repair and see the tests pass, then review the verified outcomes. All shared checks were run independently in a network-disabled, read-only, resource-limited container without live credentials. The public package can also be run with local Python.
- The original baseline failed 17 of the 26 prewritten checks. Including the four additional process checks, it failed 19 of 30. Every candidate passed all 26 prewritten checks and all four additional checks. The assistants' own regression suites were 10/10, 8/8, 10/10, and 31/31 after repair, in the order listed above. Those suites are not interchangeable scores.
- Exact measured CLI times: 326.200 seconds (5.6-SOL), 153.351 (6-SOL), 231.152 (6-Astra), 268.260 (Opus). These include session-labeling requests. This is not pure model computation time.
- **Main response usage**, before session-labeling requests: 5.6-SOL reported 37,328 input and 9,759 output tokens; 6-SOL 35,088 input and 6,033 output; Astra 45,357 input and 5,835 output. The SOL receipts reported zero cached input. Astra's receipt reported no cached input or cache writes. A “token” is a piece of text counted by the provider, not a measure of quality. For Claude's three main requests the CLI reported 6 uncached input, 4,202 cache-read input, 94,874 cache-written input, and 31,086 output; its very small uncached-input figure must **not** be mistaken for the total work it read. Output includes the reported internal thinking/reasoning tokens where provided.
- **Extra session-labeling usage:** Each SOL candidate had three auxiliary requests totaling 1,287 input and 39 output tokens; the original SOL receipts did not identify their model, so we do not assign those to the candidate model. Astra had 1,287 input and 43 output on the same auxiliary route. Claude's three title requests reported 6 uncached input, 9,296 cache-read input, 4,648 cache-written input, and 295 output. There is no sound dollar comparison from these records.
- The Astra/Opus controller finished both candidates and all checks, but exited nonzero after saving results because its *final summary print* had a typo. That reporting typo was corrected and checked separately; model calls were not repeated. It does not change the saved test outcomes, but the complete controller process did not end cleanly on that run.

To repeat the checks from this directory with Python 3.10+ (the original isolated test run used Python 3.12), run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=baseline python3 -m unittest discover -s tests -v   # expected failures: 19
for model in gpt-5.6-sol gpt-6-sol gpt-6-astra claude-opus-5-5; do
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="candidates/$model" python3 -m unittest discover -s tests -v
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="candidates/$model" python3 -m unittest discover -s "candidates/$model" -p 'test_candidate.py' -v
done
```

The baseline failing is expected; it proves these checks catch the original problem. The four candidate runs above should pass. This package is a transparent, sanitized demonstration—not the original private prompt, a live integration test, or a production release.
