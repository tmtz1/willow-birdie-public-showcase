# GPT-5.6-SOL vs GPT-6-SOL: receipt-validation code test

**Result:** Both candidates fixed the tested defect on their first implementation attempt and passed the same frozen acceptance suite (26/26) plus four added subprocess checks (4/4). GPT-6-SOL had lower measured CLI wall-clock time and fewer main-model tokens in this single run. This is a narrow result, not a general model ranking.

## The real-world task

The task came from an existing local prototype of a Buzz reply helper: harden its success reporting so a successful process exit alone cannot be mistaken for a confirmed send. The helper must require a valid affirmative JSON receipt with an event ID, while preserving input, trust-boundary, timeout, and duplicate-attempt protections.

This is a real-code, operationally grounded task—not a toy function invented for the benchmark. Important boundary: the source was a local prototype, not verified as the currently installed remote service. No live Buzz CLI/relay was called and no message was sent. The added subprocess checks used a real Python child process as an offline sender substitute; they do not establish integration with Buzz itself.

## Method

- Same sanitized starting fixture, requirements, provider (`openai-codex`), exact candidate IDs (`gpt-5.6-sol`, `gpt-6-sol`), high reasoning setting, and bounded three-call workflow per candidate: tests, implementation after failing-test feedback, then review.
- Candidate code ran in a network-disabled, read-only, resource-limited Docker container without live credentials or a Docker socket.
- Original benchmark baseline: the frozen acceptance suite had 26 tests and 17 expected failures attributable to missing receipt validation. The public package adds the four subprocess cases; running all 30 public acceptance-plus-subprocess tests against the baseline produces 19 expected failures (17 receipt-contract failures plus two subprocess confirmation failures).
- Independent post-generation subprocess checks are reported separately; they were not retroactively added to the frozen score.
- The public fixture replaces channel identifiers and host paths with synthetic placeholders. The benchmark harness, raw prompts/responses, internal role text, credentials, and provider receipts are not published.

## Results

| Candidate | Candidate regression tests | Frozen acceptance | Added subprocess checks | Measured CLI time | Main-model tokens (uncached input / cached input / output) |
|---|---:|---:|---:|---:|---:|
| GPT-5.6-SOL | 10 methods; failed on baseline, passed after patch | 26/26 | 4/4 | 326.200 s | 37,328 / 0 / 9,759 |
| GPT-6-SOL | 8 methods; failed on baseline, passed after patch | 26/26 | 4/4 | 153.351 s | 35,088 / 0 / 6,033 |

Both first implementation attempts passed their own regression suites and the identical independent acceptance suite. The four subprocess cases covered a valid receipt with whitespace/extra fields, a rejected receipt plus duplicate suppression, nonzero exit despite a valid receipt, and malformed-output redaction. Every subprocess case also asserted that stdin arrived literally and without shell expansion. They exercised a Python subprocess substitute, not the Buzz sender or relay.

Elapsed time is wall-clock CLI invocation time, including startup, provider wait, and auxiliary work—not pure inference latency. One run, no repetitions or warmed/cold-cache series; parallel provider load may differ. Main-model token usage is reported separately from title-generation overhead (1,287 input + 39 output per candidate across three auxiliary calls); the receipt did not identify the auxiliary model, so those tokens are not attributed to either candidate. No verified dollar comparison is available.

## Interpretation and limits

The measured result favors GPT-6-SOL on elapsed time and main-model token count for this task; correctness was tied. One narrow run does not establish general superiority, model judgment, full autonomous-agent behavior, or production readiness. Both offline candidate patches passed; production remains a separate integration, review, and approval decision. No production configuration was changed.

## Reproducible fixture

- `baseline/reply.py` — sanitized pre-fix fixture.
- `tests/` — frozen acceptance contract and offline subprocess checks.
- `candidates/` — candidate implementations and their regression tests.

Run candidate checks from this directory (Python 3.10+):

```bash
PYTHONPATH=candidates/gpt-5.6-sol python3 -m unittest discover -s tests -v
PYTHONPATH=candidates/gpt-6-sol python3 -m unittest discover -s tests -v
PYTHONPATH=candidates/gpt-5.6-sol python3 -m unittest discover -s candidates/gpt-5.6-sol -p 'test_candidate.py' -v
PYTHONPATH=candidates/gpt-6-sol python3 -m unittest discover -s candidates/gpt-6-sol -p 'test_candidate.py' -v
```

The baseline is expected to fail the receipt-validation acceptance cases; use it only to confirm the regression tests detect the original defect. These are focused benchmark tests, not a canonical full-suite or production-integration certification.
