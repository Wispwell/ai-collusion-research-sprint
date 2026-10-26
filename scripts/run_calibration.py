"""Run calibration conditions.

    PYTHONPATH=src python scripts/run_calibration.py free-stranger blocked-offer --runs 30 --concurrency 10
    PYTHONPATH=src python scripts/run_calibration.py blocked-offer --version v4 --model openai/gpt-5.6-terra

Each run gets a fresh sandbox under work/sandboxes/ and its own trace database
under work/traces/, both outside anything the agent can reach. The measured
record of each run goes to experiments/<version>/results/logs/[<model>/]<condition>/run-NN.json:
v3 used one model (no model directory); v4 adds one directory per model. Existing results are
skipped, so an interrupted batch can be resumed.
"""

import argparse
import asyncio
from pathlib import Path

from protonous import Session

from harness.testbed import CONDITIONS, MODEL, run_once, save

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"


def slug(model: str) -> str:
    return model.replace("/", "__")


async def one(condition: str, index: int, gate: asyncio.Semaphore, version: str, model: str) -> None:
    logs = ROOT / "experiments" / version / "results" / "logs"
    if version != "v3":
        logs = logs / slug(model)
    out = logs / condition / f"run-{index:02d}.json"
    if out.exists():
        return
    async with gate:
        traces = WORK / "traces"
        traces.mkdir(parents=True, exist_ok=True)
        tag = f"{version}-{slug(model)}-{condition}-{index:02d}"
        db = traces / f"{tag}.db"
        db.unlink(missing_ok=True)
        with Session.create(tag, {"version": version, "model": model, "condition": condition, "index": index}, db=db) as session:
            try:
                result = await run_once(CONDITIONS[condition], index, WORK / "sandboxes" / tag, session, model)
            except Exception as error:  # recorded in the trace db; leave no result so it reruns
                print(f"{model} {condition} run {index}: {type(error).__name__}: {error}")
                return
        save(result, out)
        writes = [e.path for e in result.events if e.tool == "write_file"]
        print(f"{model} {condition} run {index}: {result.steps} steps, {result.stop}, writes {writes}, cost {result.cost:.4f}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("conditions", nargs="+", choices=sorted(CONDITIONS))
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--version", default="v3")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    gate = asyncio.Semaphore(args.concurrency)
    jobs = [one(c, i, gate, args.version, args.model) for c in args.conditions for i in range(args.start, args.start + args.runs)]
    await asyncio.gather(*jobs)


if __name__ == "__main__":
    asyncio.run(main())
