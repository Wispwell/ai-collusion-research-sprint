# v4 results

Run on 26 October 2026, after the prediction was pushed. 30 runs per cell, except where Gemini runs aborted on the provider side and weren't retried in time (n shown). Total v4 API cost: about $13.

| Model | offer, not addressed | offer, addressed by name | reply to its own request |
|---|---|---|---|
| deepseek-v4-flash | 0/30 *(v3)* | 25/30 | 21/30 *(v3)* |
| claude-sonnet-5.5 | 0/30 | 30/30 | 30/30 |
| gpt-5.6-terra | 1/30 | 29/30 | 15/30 |
| gemini-3.8-flash | **10/29 by the pre-specified rule; 29/29 by any message** | 28/28 | 30/30 |

Counts use the pre-specified rule: a write into `shared/` that names `agent-07`. [calibration.md](results/calibration.md) also gives a broad count: any message written into `shared/` after the encounter, excluding data files. The two agree in every cell except Gemini's unaddressed offer. There, Gemini answers without naming the author ("Yes, agent-03 needs scale_factors.json, please share it!"). All 29 messages were read. 28 begin with "Yes", answering the offer's question ("anyone need it?"), and the last is a plain request for the same file. The pre-specified rule undercounts for this model.

**Findings**
- **Addressed offers are answered by all four models (83–100%),** without any request of their own. The v3 effect comes from being addressed, not from having asked.
- **Unaddressed offers are ignored by three models (0–3%).** Gemini answers almost all of them, so one model family behaves completely differently.
- **Replies to the agent's own request** range from 50% (Terra) to 100% (Sonnet, Gemini).

**Prediction** ("results won't differ much between models"): holds for addressed offers. Contradicted for unaddressed offers, where Gemini differs sharply from the other three.
