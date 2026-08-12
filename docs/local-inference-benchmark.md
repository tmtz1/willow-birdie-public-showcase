# Local inference benchmark: BirdieRog

## Overview

BirdieRog is a local GPU inference worker used for private model evaluation and bounded helper workloads. The purpose of the benchmark was not to crown a model based on one impressive answer. It was to compare practical behavior under the same local serving stack and identify where each candidate broke.

The results below are historical benchmark evidence. They are useful for routing decisions, not universal claims about model intelligence.

## Hardware and serving profile

The benchmark host used:

- NVIDIA GeForce RTX 5070
- Approximately 12 GB of GPU memory
- Approximately 46 GB of system RAM
- llama.cpp server with CUDA acceleration
- GGUF model files
- OpenAI-compatible local API for the agent benchmark
- Native local chat API for a separate modality/configuration probe

The host was intentionally treated as a constrained local inference machine. Larger models could use system RAM or become unstable under context and offload pressure. That constraint was part of the test, not a footnote.

No credentials, API keys, passkeys, private endpoints, internal addresses, or host-specific paths are included here.

## What the benchmark tested

The main seven-test matrix exercised:

1. Exact-output compliance.
2. Strict JSON behavior.
3. Small coding task.
4. Privacy-aware routing judgment.
5. False-premise handling.
6. Known-fact response behavior.
7. Native tool calling.

A separate earlier eight-test matrix measured agent behavior, tool use, structured output, judgment, and latency. Scores from the two matrices should not be mixed as if they were one test.

The benchmark recorded pass/fail behavior, response time, visible output, finish reason, and tool-call results. It also recorded server disconnects, empty output, output-budget exhaustion, and formatting failures.

## Seven-test candidate results

| Model | Result | Total test time | Practical reading |
|---|---:|---:|---|
| Gemma 3 12B | 7/7 | 4.93 s | Fast and successful on this matrix; needs separate long-run and tool-depth validation. |
| Ministral 3 14B Instruct | 7/7 | 21.40 s | Strong local candidate; good tool/privacy behavior, but output formatting needed correction. |
| Devstral Small 2 24B | 7/7 in the broad run | 64.74 s | Passed the broad matrix, but a separate run exposed server instability during coding under the available memory margin. |
| Qwen3 8B | 7/7 | 128.59 s | Reliable on the broad matrix, but slower than the best smaller candidates in that run. |
| Qwen3 14B Abliterated | 7/7 | 122.17 s | Passed the broad matrix; factual-honesty concerns remained in the separate chat bake-off. |
| Qwen3 8B Abliterated | 7/7 | 142.37 s | Passed the broad matrix; not automatically suitable for factual chat. |
| Qwen3 14B | 7/7 | 143.69 s | Passed the broad matrix; slower and subject to the same honesty caveat. |
| Ministral 3 14B Reasoning | 7/7 | 232.16 s | Technically capable, but reasoning overhead was too high for live conversational use. |
| Qwen3 14B Heretic | 7/7 | 535.26 s | Passed the broad matrix, but latency was operationally poor. |
| Qwen3 32B Heretic | 6/7 | 777.53 s | Failed one test and was far too slow for the intended local assistant role. |

The broad run was completed with the production service restored afterward and its health verified. Model files were not automatically deleted based on these results.

## Earlier comparison results

A separate eight-test comparison produced these recorded scores:

| Model | Score | Median latency | Result |
|---|---:|---:|---|
| Qwen3 8B Q8 | 8.00/8 | 3.859 s | Best verified local agent in that matrix. |
| GPT-OSS 20B | 7.00/8 | 5.636 s | Strong candidate, but failed the three-step tool chain. |
| Mistral Small 3.2 24B | 6.33/8 | 7.590 s | Good structured output; weaker agent behavior. |
| Qwen3.5 35B-A3B | Separate reasoning probe | Fast when successful | Reasoning/output-channel behavior required correction before it could be judged cleanly. |

These results explain why there was no single “winner” across every use case. Qwen3 8B was the strongest verified general local agent in one matrix. Ministral 3 14B Instruct was the most promising newer replacement candidate. A model that passes a broad smoke matrix can still fail a factual-honesty bake-off.

## Notable errors and corrections

### Markdown-wrapped JSON and code

Ministral 3 14B Instruct often returned semantically correct JSON or code wrapped in Markdown and explanatory prose. That is acceptable for a human reader but fails strict machine-to-machine output contracts.

Correction:

- Tighten prompts to request raw output only.
- Validate output after generation.
- Strip no formatting silently when the contract requires exact output; reject and retry through an explicit bounded path instead.
- Keep the model out of contracts where strict serialization is mandatory until the behavior is stable.

### Reasoning consumed the answer channel

The Ministral reasoning model used substantial time and output budget on internal reasoning. Its code case produced empty visible output with a length finish reason even though other tests passed.

Phi-4 Reasoning Plus showed a more severe version of the same problem: exact and JSON probes consumed the output budget while the model repeated reasoning instead of returning the requested answer.

Correction:

- Separate reasoning and final-answer channels where the server and model support it.
- Set an explicit reasoning budget.
- Test visible output, not just request completion.
- Treat empty output and length termination as failures.

### Large-model runtime instability

Devstral Small 2 24B passed the exact and JSON probes in one constrained run, then the server disconnected during the code test. The model file was complete; the failure occurred during serving under the available GPU/RAM and offload conditions.

Correction:

- Record the server failure rather than calling it a pass.
- Restore the known-good production worker after candidate tests.
- If revisiting the model, test a smaller context and explicitly measured offload settings in a separate run.

### API modality mismatch

A Qwen3.5 9B probe sent through the OpenAI-compatible route did not reliably suppress reasoning when `think:false` was requested. The result was empty visible output with the completion budget consumed.

The native local chat API accepted the same conceptual setting and returned visible text. That isolated the first problem as an integration/configuration mismatch rather than proof that the model could not answer.

The second problem remained: visible native responses still contained fabricated factual material in the honesty bake-off.

## Operational conclusions

- Use benchmark scores as routing evidence, not as a general intelligence ranking.
- Keep a small, fast, verified local model for routine structured work.
- Treat reasoning models as specialized tools until visible-output behavior and latency are proven.
- Keep factual research behind retrieval or another evidence mechanism.
- Do not expose a local chatbot to factual public use merely because it is fast or passes a tool test.
- Do not delete a model solely because it failed one benchmark; distinguish redundancy from specialization.

The useful outcome was not a shiny leaderboard. It was a map of which models were fast, which were tool-capable, which were honest about uncertainty, and which simply found new ways to waste the afternoon.

## Scope and limitations

This was a local, task-specific benchmark using selected prompts and a particular serving configuration. It does not establish broad model quality, safety, or factual reliability. Model versions, quantization, context length, server flags, prompt wording, and hardware can change the result.

The benchmark documentation intentionally omits raw prompts where they could expose private operational context, raw transcripts, credentials, private infrastructure details, and model files.
