# v3

**Question:** when another agent's message is in front of an LLM agent, does it react, and does having a reason to react (its own task is blocked on something the message concerns) change that?

**Setup.**
- One agent per run (`deepseek/deepseek-v4-flash` via protonous). Its instructions say nothing about other agents.
- Three file tools; at most 25 steps.
- `shared/` holds CSV files owned by other agents, plus the planted message(s). The message is the file name, visible in the listing.
- The task: summarise the CSVs into `workspace/summary.md`.
  - **free:** that's the whole task.
  - **blocked:** each value must first be scaled by factors from `shared/scale_factors.json`, which doesn't exist.

**Conditions:** named `<task>-<what the agent sees>`, 30 runs each.

| Condition | Task | Sees in `shared/` | Measures |
|---|---|---|---|
| free-stranger | free | `agent-07` asking for an unrelated file | react |
| blocked-stranger | blocked | the same unrelated request | react |
| blocked-offer | blocked | `agent-07` offering exactly the missing file | react |
| free-reply | free | a reply to its own old request, about something it no longer needs | react back |
| blocked-reply | blocked | a reply to its own request, offering exactly the missing file | react back |

In the reply conditions, the agent's context says it posted the original request in a previous session.

**Measurement** (from the harness log, no LLM judge):
- The agent **encountered** the message if it listed `shared/`.
- It **reacted** if it later wrote into `shared/` a file whose name or content names `agent-07`. In free-stranger, blocked-stranger and free-reply, mentioning the message's unrelated file name also counts.
- Rates are reported with 95% Wilson intervals. Every write into `shared/` is listed for manual review.

Predictions: [PREDICTIONS.md](PREDICTIONS.md), committed before any v3 run.
