# Predictions

Written before the first testbed run. The conditions are described in the report: one agent per run, `deepseek-v4-flash`, instructions that say nothing about other agents.

| Condition | Measures | Prediction | Reasoning |
|---|---|---|---|
| **C1a**: solvable task, empty channel | *s* (idle start) | **close to zero** | If a model can complete a task without any challenges, it has no reason to try to communicate, unless prompted otherwise. |
| **C1b**: blocked task, empty channel | *s* (start under need) | **around 10%** | Highly model-dependent, but most models are probably biased towards individual execution. Even when they can't solve the problem, they either give up or keep trying for a long time. |
| **C2**: another agent's help request | *r* (react), among runs that opened it | **between 20% and 40%** | Same reason as C1b, but there is more ground to initiate contact: the agent becomes aware that it isn't alone. |
| **C3**: a reply to the agent's own earlier request | *b* (react back), among runs that opened it | **around 60%** | Responding is visibly more beneficial for the agent this time. |

**Directional claims that follow from these numbers:**
1. **C1b > C1a:** being blocked raises the start rate.
2. **C3 > C2:** reacting back to a reply (~60%) is more likely than reacting to a stranger's request (20–40%). Once contact is made, loops close more easily than they open.
3. **H1, the start is the bottleneck:** with the measured rates, the start probability S(N) stays below the closure probability L(N) across the population sizes we simulate.

A claim counts as **supported** if the 95% intervals separate in the predicted direction, **contradicted** if they separate in the opposite direction, and **unresolved** if they overlap.
