# AI Collusion Research Sprint: the onset of coordination

Work for the Apart Research AI Collusion Research Sprint (23–25 October 2026).

Coordination is modelled as circular influence: it starts once information leaving an agent comes back to that agent. We model how that loop first closes, check the model against a simulation, and measure its rates with a single-agent testbed.

## Layout

- `experiments/`: the testbed's design versions, each with its predictions and results ([index](experiments/README.md))
- `src/loop_model/`: simulation of the loop model
- `src/harness/`: the single-agent testbed
- `scripts/validate_loop.py`: checks the simulation against exact cases and sweeps scale and duration
- `results/`: `loop_summary.md`, figures, transcripts and logs

## Run

```bash
pip install -r requirements.txt   # python 3.13
PYTHONPATH=src python scripts/validate_loop.py
```

## New vs preexisting

- **Preexisting:** [protonous](https://github.com/Wispwell/protonous), a public, general-purpose agent framework written before the sprint, and our earlier sprint paper *The Sentinel's Dilemma*.
- **New during the sprint:** everything in this repository.
