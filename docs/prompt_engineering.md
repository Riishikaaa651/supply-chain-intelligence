# Prompt Experiments

Rule used everywhere: **Python calculates the numbers, the LLM only explains them.**

## Risk briefing

| Version | What went wrong / what changed |
|---|---|
| v1 | Copied the input tables back, gave generic actions, and did its own arithmetic wrong (orders total came out as 7,938 and 8,938 in two runs; the correct sum is 7,988). Blamed First Class itself instead of its tight 1-day promise. |
| v2 | Added `build_facts()` so Python pre-calculates the numbers (late rate, gap, counts). Added rules, a fixed format and a word limit. Arithmetic errors disappeared. Still listed the best mode (Standard Class) as a risk and suggested an unsupported action. |
| v3 | Added: list risks worst-first, never list the best mode as a risk, explain cause only via promised vs actual days, every action must follow from a number, plus one few-shot style example with fictional numbers. |

**Model comparison (v2 and v3 on both models):** gpt-oss-120b + v3 scored best. gpt-oss-20b + v3 added a third action and guessed a "systemic issue" that the data does not show.
**Chosen:** gpt-oss-120b, v3.

## What-if scenarios

| Version | What went wrong / what changed |
|---|---|
| v1 | Long, tables everywhere, and drifted into cost speculation that is not in the data. |
| v2 | Short and correct, but the answer was one word ("Mixed.") and it never said the promised window changes (1 day to 4 days), which is part of why lateness drops. |
| v3 | Answer is one full sentence naming the trade-off, bullets show before -> after, states the promise change, and includes the assumption caveat. |

**Chosen:** v3.

## Bugs and lessons

- Before/after were rounded separately from the change, so the numbers did not add up (change showed 1,072, not 1,073). Fix: round first, then subtract.
- The Llama models were not available on my Groq key. Listing models with the API (`client.models.list()`) gave the exact usable IDs.
- Changing the prompt improved results more than changing the model size.
- LLMs are unreliable at arithmetic, so all numbers come from SQL and Python.