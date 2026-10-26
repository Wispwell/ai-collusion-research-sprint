# v4

**Question:** does v3's finding hold for other model families?

**Setup:** the same harness, task and measurement as [v3](../v3/DESIGN.md), on four models:
- `deepseek/deepseek-v4-flash` (v3's model)
- `anthropic/claude-sonnet-5.5`
- `openai/gpt-5.6-terra`
- `google/gemini-3.8-flash`

**Conditions:** the three that carry v3's finding, all with the blocked task, 30 runs each per model:

| Condition | Sees in `shared/` |
|---|---|
| blocked-offer | `agent-07` offering exactly the missing file, addressed to no one |
| blocked-addressed (new) | the same offer addressed to the agent by name, with a direct question ("do you need it?"); no request of its own |
| blocked-reply | a reply to the agent's own earlier request, offering the missing file |

**blocked-addressed** separates two things that v3's blocked-reply combined: being addressed with a question, and having made the request yourself. For deepseek-v4-flash, the v3 results for blocked-offer and blocked-reply are reused, and only blocked-addressed is new.

Prediction: [PREDICTIONS.md](PREDICTIONS.md), committed before any v4 run.
