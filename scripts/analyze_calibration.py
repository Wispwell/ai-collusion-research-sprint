"""Measure r and b from the calibration logs.

    PYTHONPATH=src python scripts/analyze_calibration.py            # v3
    PYTHONPATH=src python scripts/analyze_calibration.py --version v4

Encounter: the agent listed `shared/` (the message is visible in the listing).
Reaction (pre-specified rule): a later write into `shared/` whose path or content
names one of the condition's tokens. "Any message" (broad rule) counts any later
message written into `shared/`, excluding data files; it exists because some
agents answered an offer without naming its author ("Yes, agent-03 needs it").
Writes to `workspace/` never count.

Writes experiments/<version>/results/calibration.md (rates with 95% Wilson intervals, plus
every write into `shared/` for manual audit) and a markdown transcript per reacting run.
"""

import argparse
import json
import math
from pathlib import Path

from harness.testbed import CONDITIONS

ROOT = Path(__file__).resolve().parent.parent


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def in_shared(path: str) -> bool:
    return path.strip("./").split("/")[0] == "shared"


def any_message(run: dict) -> bool:
    """Broad rule: after the encounter, the agent wrote any message into shared/ (not a data file)."""
    events = run["events"]
    first_seen = next((i for i, e in enumerate(events) if e["tool"] == "list_dir" and e["ok"] and e["path"].strip("./") == "shared"), None)
    if first_seen is None:
        return False
    def is_data(path: str) -> bool:
        return path.strip("./") == "shared/scale_factors.json" or path.endswith(".csv")

    return any(e["tool"] == "write_file" and in_shared(e["path"]) and not is_data(e["path"]) for e in events[first_seen + 1:])


def measure(run: dict, tokens: tuple[str, ...]) -> tuple[bool, bool, list[dict]]:
    events = run["events"]
    first_seen = next((i for i, e in enumerate(events) if e["tool"] == "list_dir" and e["ok"] and e["path"].strip("./") == "shared"), None)
    posts = [e for e in events if e["tool"] == "write_file" and in_shared(e["path"])]
    if first_seen is None:
        return False, False, posts
    later = [e for e in events[first_seen + 1:] if e["tool"] == "write_file" and in_shared(e["path"])]
    reacted = any(any(t.lower() in (e["path"] + (e["content"] or "")).lower() for t in tokens) for e in later)
    return True, reacted, posts


def transcript(run: dict, path: Path) -> None:
    lines = [f"# {run['condition']} run {run['index']:02d}", "", f"{run['steps']} steps, stop: {run['stop']}", ""]
    for e in run["events"]:
        lines.append(f"- step {e['step']}: `{e['tool']}` `{e['path']}`" + ("" if e["ok"] else " (failed)"))
        if e["content"]:
            lines += ["", "  ```", *("  " + line for line in e["content"].splitlines()), "  ```", ""]
    lines += ["", "**Final message:**", "", run["final"] or "(none)", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def tally(logs: Path, transcripts: Path, label: str, rows: list[str], audit: list[str]) -> None:
    for name, condition in CONDITIONS.items():
        files = sorted((logs / name).glob("run-*.json"))
        if not files:
            continue
        seen = reacted = broad = 0
        for f in files:
            run = json.loads(f.read_text())
            s, r, posts = measure(run, condition.tokens)
            seen += s
            reacted += r
            broad += any_message(run)
            for e in posts:
                audit.append(f"- **{label}{name} run {run['index']:02d}**{' (reaction)' if r else ''}: `{e['path']}`: {(e['content'] or '').strip()[:200]!r}")
            if r:
                transcript(run, transcripts / name / f"run-{run['index']:02d}.md")
        lo, hi = wilson(reacted, seen)
        rate = reacted / seen if seen else math.nan
        rows.append(f"| {label}{name} | {len(files)} | {seen} | {reacted} | {rate:.2f} | [{lo:.2f}, {hi:.2f}] | {broad} |")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v3")
    args = parser.parse_args()
    results = ROOT / "experiments" / args.version / "results"
    logs = results / "logs"
    rows = ["# Calibration results", "", "| condition | runs | encounters | reactions | rate | 95% CI | any message |", "|---|---|---|---|---|---|---|"]
    audit = ["", "## Every write into shared/ (for manual audit)", ""]
    if args.version == "v3":
        tally(logs, results / "transcripts", "", rows, audit)
    else:
        for model_dir in sorted(p for p in logs.iterdir() if p.is_dir()):
            model = model_dir.name.replace("__", "/")
            tally(model_dir, results / "transcripts" / model_dir.name, f"{model} · ", rows, audit)
    if len(audit) == 3:
        audit.append("(none)")
    text = "\n".join(rows + audit) + "\n"
    (results / "calibration.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
