# Follow-up v1: deep JSON error normalization

Dated September 24, 2026 (America/Chicago). This is maintainer hardening, **not new model output** and not a change to the historical scores.

On Python 3.12.3, 10,000 nested arrays cause the frozen GPT-6-SOL candidate to leak `RecursionError`, while GPT-5.6-SOL returns its sanitized `RuntimeError`. The regression checks the **exact type** because `RecursionError` is itself a `RuntimeError` subclass. It also verifies the failed attempt stays blocked.

The GPT-6-SOL follow-up copy adds `RecursionError` to the parser exception handler. The GPT-5.6-SOL follow-up copy is unchanged. Frozen `candidates/`, shared historical tests and baseline remain byte-identical, checked against `historical-hashes.json`.

A Python 3.14.7 probe did not raise a parser recursion exception for the same input; the original candidate therefore already rejected the parsed non-object safely there. This is runtime-dependent, not evidence that the Python 3.12 finding was invalid. CI exercises both versions.

From the benchmark root, `python3.12 verify.py` checks all original suites, expected baseline failures, both follow-up copies on the original 30 tests, and the new regression separately. No live message is sent.
