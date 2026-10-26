# Prompt Engineering: GenAI Layer

This document explains how the GenAI layer of **Supply Chain Decision Intelligence** works, how the prompts were designed, and how each prompt version was tested and improved.

---

## 1. What the GenAI layer does

The ML models (delay and shortage) give a number. A logistics manager needs an **explanation** and a way to ask "what if...". The GenAI layer turns the numbers stored in the database into short, plain-language answers.

It produces 4 kinds of output:

| Kind | Input | Output |
|---|---|---|
| `delay_briefing` | One order | 3-line briefing on delay risk |
| `delay_whatif` | One order + a question | Up to 4 lines comparing the scenario |
| `shortage_briefing` | One order / product | 3-line briefing on shortage risk |
| `shortage_whatif` | One order / product + a question | Up to 4 lines comparing the scenario |

The LLM **explains** the model output. It does not change it and it does not re-run the model.

---

## 2. How it works (flow)

```
order_item_id (+ question)
        |
        v
get_explanation()                     src/genai/briefing.py
        |
        |-- 1. check llm_briefings table (cache)  --> found? return saved answer
        |
        |-- 2. get facts from SQLite              src/database/queries.py
        |        get_delay_facts / get_shortage_facts / get_delay_context
        |
        |-- 3. build_prompt()                     src/genai/prompt_templates.py
        |        (prompt version comes from config.yaml)
        |
        |-- 4. ask_llm()                          src/genai/llm_client.py
        |        (Groq API)
        |
        |-- 5. format_lines()  -> one sentence per line
        |
        '-- 6. save answer in llm_briefings (cache)
```

### Settings (`config.yaml`)

```yaml
llm:
  provider: groq
  model: openai/gpt-oss-120b
  temperature: 0.2
  max_tokens: 2000
  timeout_seconds: 30

prompts:
  active_delay_briefing_version: v3
  active_delay_whatif_version: v4
  active_shortage_briefing_version: v3
  active_shortage_whatif_version: v4
```

- **Low temperature (0.2):** answers stay factual and consistent.
- **Versions in config:** switching a prompt version is a one-line change, with no code edit.
- **API key** is stored in `.env` (never pushed to GitHub).

---

## 3. Design principles

These rules are in the system prompt or in the templates:

1. **Only use the numbers given.** "Use ONLY the numbers given to you. Never invent numbers."
2. **Give the LLM facts from the database**, not just a risk label. A label alone gives a generic answer.
3. **Give context for the numbers.** A 41% delay probability means little without knowing the overall late rate is 57.3%.
4. **Never call the shortage score a probability.** It is a ranking score (the real shortage rate in the data is only 2.9%, and balanced class weights inflate the scores).
5. **Do not give a new prediction in what-if answers.** The model must be re-run for an exact value, and the answer says so.
6. **Fixed output shape.** 3 lines for a briefing, at most 4 lines for a what-if, one sentence per line.
7. **Say "cannot answer" instead of guessing** when the numbers do not cover the question.

### Facts passed to the LLM

| Prompt | Facts |
|---|---|
| Delay | shipping mode, region, category, delay probability, risk level, mode and region average delay (+ std), overall late rate, late rate per shipping mode, late rate per region |
| Shortage | product, category, shortage score, risk level, average demand, demand std, quantity deviation, number of past orders |

Risk levels:
- **Delay:** Low below 45%, Medium 45% to 75%, High above 75% (probability bands).
- **Shortage:** High = top 10% of all orders by score, Medium = next 20%, Low = rest (percentile bands).

---

## 4. Version history

Every version was tested on the same sample orders (`order_item_id 2` for delay, `176147` for shortage), so the only thing that changed between runs was the prompt.

### Active versions: briefings **v3**, what-ifs **v4**

### `delay_briefing`

| Version | Change | Why |
|---|---|---|
| v1 | First version: order details, delay probability, risk level, mode and region average delay, reliability scores. | Baseline. |
| v2 | Added overall late rate (57.3%), late rate per shipping mode, risk band definitions. Removed reliability scores. Added the rule: the explanation must match the risk level. | v1 said the region was "driving the higher delay chance" although the risk was **Low**. The LLM also copied reliability scores (-2.00) without knowing what they mean. A 41% probability had no baseline to compare with. |
| v3 | Each sentence on its own line. | Easier to read on the dashboard. |

### `delay_whatif`

| Version | Change | Why |
|---|---|---|
| v1 | Order details + question. | Baseline. |
| v2 | Added overall late rate and late rate per shipping mode. | v1 answered "we have no First Class data to compare". With the table, the answer became First Class 100% vs Standard Class 39.8%. |
| v3 | One sentence per line, compare current and new mode with the overall rate. | Readability. |
| v4 | Added late rate per region. New rules: compare extra days with the delay std; say "cannot answer" if the numbers do not cover it; say so if the new mode or region is the same as the current one. | In v3, "2 days longer" produced "closer to Second Class (79.8%)", which is not supported by any number. The Western Europe question ignored the region and repeated Standard Class rates. |

### `shortage_briefing`

| Version | Change | Why |
|---|---|---|
| v1 | Score marked as "ranking score, NOT a probability". | Stop the LLM from saying "73% chance of shortage". |
| v2 | Added meaning of the risk levels. New rule: if past orders are fewer than 5, say the history is limited. | The score is less reliable for products with little history. |
| v3 | One sentence per line. Do not invent quantities or time periods; the standard deviation may be used as a buffer. | v2 produced "safety stock equal to one month's average demand". There is no monthly data. |

### `shortage_whatif`

| Version | Change | Why |
|---|---|---|
| v1 | Order details + question. | Baseline. v1 mentioned "supply limits", which we have no data on. |
| v2 | Rule: no supply, lead time or capacity. | Stop invented context. v2 answers became vague. |
| v3 | Simple arithmetic allowed (new demand, change compared with std). One sentence per line. | The LLM can now say "285.5 units, 1.6 times the std". |
| v4 | One line saying whether the change would **likely** raise or lower the shortage risk. | v3 only did arithmetic and never said what it means for risk. |

---

## 5. Testing method

1. Fix two sample orders and run every prompt version on the same inputs.
2. Read the answers and check every number by hand. Examples verified:
   - 237.9 x 1.2 = 285.5, and 285.5 - 237.9 = 47.6 (about 1.6 x std 30.2)
   - 237.9 x 0.7 = 166.5, and 71.4 is about 2.4 x std
   - 237.9 x 2 = 475.8, std x 2 = 60.4 (about 25% of the average)
   - 237.9 x 1.5 = 356.9
3. Look for three kinds of problem: logic that contradicts the risk level, invented facts, and wrong format.
4. Fix the prompt, bump the version (never edit an old version), and compare the old and new answers side by side.

### What-if questions (stored in `config.yaml`, used by the dashboard)

**Delay**
1. What if we ship this order with First Class instead?
2. What if we switch this order to Same Day shipping?
3. What if we upgrade to Second Class?
4. What if we switch to Standard Class?
5. What if this order is sent to Western Europe instead?
6. What if the delivery takes 2 days longer than scheduled?

**Shortage**
1. What if demand for this product rises by 20% next week?
2. What if demand drops by 30%?
3. What if demand doubles?
4. What if the demand variability (standard deviation) doubles?
5. What if demand rises by one standard deviation?
6. What if demand rises by 50%?

---

## 6. Caching

Answers are saved in the `llm_briefings` table.

| Column | Meaning |
|---|---|
| `kind` | delay_briefing, delay_whatif, shortage_briefing, shortage_whatif |
| `entity_key` | the `order_item_id` |
| `prompt_version` | v1, v2, v3, v4 |
| `question` | the what-if question (empty for briefings) |
| `response` | the saved answer |

- The cache key includes the **prompt version**, so a new version never returns an answer written by an old prompt, and rolling back to an old version reuses its saved answers.
- First call about 3 seconds, repeated call about 0.01 seconds.
- Empty answers are never saved. A reasoning model can run out of `max_tokens` and return nothing, so `get_explanation` raises an error with a hint to raise `max_tokens`.

---

## 7. Limitations

- What-if answers are **explanations, not new predictions**. The model is not re-run.
- "Likely raise / likely lower" in shortage answers is a common-sense direction, not verified by re-running the model.
- The shortage score is a ranking score, not a probability.
- The delay model mostly learns the shipping mode. Region barely changes the result (Western Europe 58.5% vs South America 57.2%).
- Products with very little order history get less reliable scores. The briefing says so when past orders are fewer than 5.
- The LLM is a reasoning model, so tokens used for thinking count towards `max_tokens`.

---

## 8. Interview questions

**Why did you version your prompts?**
Each change was a fix for a specific problem I saw in the output. Versions let me compare old and new answers on the same input, roll back with one config line, and keep old cached answers valid.

**How do you stop the LLM from making up numbers?**
Three ways: the system prompt says to use only the given numbers, the facts come from the database, and the prompts forbid inventing quantities or time periods. I also checked the arithmetic in the answers by hand.

**Why not let the LLM give the new probability in what-if answers?**
The LLM cannot run the model, so any number it gave would be a guess. It compares scenarios using real historical rates and says the model must be re-run for an exact value.

**Why is the shortage score not shown as a percentage?**
The real shortage rate is 2.9% but the scores average 0.39, because of balanced class weights. It ranks products correctly but it is not a probability.

**Why cache the answers?**
To cut latency (3 seconds to 0.01 seconds) and API cost. The same order and question always returns the same saved answer for a given prompt version.

**How would you improve it?**
Re-run the model for fixed scenarios (for example a different shipping mode) and let the LLM explain the new number, instead of only comparing historical rates.