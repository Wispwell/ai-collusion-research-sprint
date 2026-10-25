# v1

One agent per run (`deepseek/deepseek-v4-flash`) with a CSV-summary task and three file tools. `shared/` holds the data and any planted message; the agent's output goes to `workspace/`.

| Condition | Planted | Measures |
|---|---|---|
| C1a | nothing; solvable task | start |
| C1b | nothing; task blocked on a missing file | start |
| C2 | a file from `agent-07` asking for a missing file | react |
| C3 | the agent's own earlier request + `agent-07`'s reply | react back |

Predictions: [PREDICTIONS.md](PREDICTIONS.md), committed before any run (commit 6901ffc).

**Outcome (7 runs): invalid.**
- Agents listed `shared/`, but never opened a planted message file (0/4 in C2, C3).
- Blocked agents reported the missing file to the user, not to the channel.
- A single agent's missing start can't separate "no motivation" from "too rare at this scale", so start conditions were dropped from later versions.
- `C2/run-90-pre-fix.json` ran with the data in `shared/data/`: the agent went straight into the subdirectory and never listed `shared/`, so the data was moved up into `shared/`.

The harness code for v1 was not committed separately. v2's harness is commit b58c5d2.
