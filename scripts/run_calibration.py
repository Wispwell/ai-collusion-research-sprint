"""Run calibration conditions.

    PYTHONPATH=src python scripts/run_calibration.py C2 C3 --runs 30 --concurrency 10

Each run gets a fresh sandbox under work/sandboxes/ and its own trace database
under work/traces/, both outside anything the agent can reach. The measured
record of each run goes to results/logs/<condition>/run-NN.json. Existing
results are skipped, so an interrupted batch can be resumed.
"""

import argparse
import asyncio
from pathlib import Path

from protonous import Session

from harness.testbed import CONDITIONS, run_once, save

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
LOGS = ROOT / "results" / "logs"


async def one(condition: str, index: int, gate: asyncio.Semaphore) -> None:
    out = LOGS / condition / f"run-{index:02d}.json"
    if out.exists():
        return
    async with gate:
        traces = WORK / "traces"
        traces.mkdir(parents=True, exist_ok=True)
        db = traces / f"{condition}-{index:02d}.db"
        db.unlink(missing_ok=True)
        with Session.create(f"{condition}-{index:02d}", {"condition": condition, "index": index}, db=db) as session:
            try:
                result = await run_once(CONDITIONS[condition], index, WORK / "sandboxes" / condition / f"run-{index:02d}", session)
            except Exception as error:  # recorded in the trace db; leave no result so it reruns
                print(f"{condition} run {index}: {type(error).__name__}: {error}")
                return
        save(result, out)
        writes = [e.path for e in result.events if e.tool == "write_file"]
        print(f"{condition} run {index}: {result.steps} steps, {result.stop}, writes {writes}, cost {result.cost:.4f}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("conditions", nargs="+", choices=sorted(CONDITIONS))
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    gate = asyncio.Semaphore(args.concurrency)
    jobs = [one(c, i, gate) for c in args.conditions for i in range(args.start, args.start + args.runs)]
    await asyncio.gather(*jobs)


if __name__ == "__main__":
    asyncio.run(main())
