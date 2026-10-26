"""Sanity checks for the loop model.

1. Exact cases (N = 2, fast-encounter limit) against the simulation.
2. Scale: P(first turn) vs number of agents, for seeded and spontaneous starts.
3. Duration: P(first turn) vs rho * D.

Writes figures to results/figures/ and loop_summary.md to results/.
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt

from loop_model.loop_sim import LoopParams, estimate

RESULTS = Path(__file__).resolve().parent.parent / "results"
FIGURES = RESULTS / "figures"
FAST = dict(duration=1.0, rho=5000.0)
ILLUSTRATIVE = dict(s=0.05, r=0.3, b=0.6)
EXACT_RUNS = 200_000
SWEEP_RUNS = 5_000


def start_probability(n: int, s: float, duration: float, group: int) -> float:
    """S: a starting message exists. Planted in group 1, posted at rate s per agent in group 2."""
    return 1.0 if group == 1 else 1 - math.exp(-n * s * duration)


def exact_two_agents(start: float, r: float, b: float) -> float:
    """N = 2: a start, a reaction from the other agent, a reaction back. P = S * r * b."""
    return start * r * b


EXACT_CASES = [  # (group, s, r, b); s is unused in group 1, where S = 1
    (1, None, 0.3, 0.6), (1, None, 0.7, 0.5), (1, None, 0.5, 0.9),
    (2, 0.7, 0.3, 0.6), (2, 0.7, 0.7, 0.5), (2, 0.2, 0.5, 0.9),
]


def exact_checks() -> list[str]:
    lines = ["## Exact cases (N = 2): P = S * r * b", "", f"{EXACT_RUNS} runs per cell, D = 1, rho * D = 5000.", "",
             "| start | s | S | r | b | exact | simulation | z |", "|---|---|---|---|---|---|---|---|"]
    for i, (group, s_rate, r, b) in enumerate(EXACT_CASES):
        params = LoopParams(n=2, s=s_rate or 0.0, r=r, b=b, **FAST)
        start = start_probability(2, params.s, params.duration, group)
        exact = exact_two_agents(start, r, b)
        simulated = estimate(params, group, EXACT_RUNS, seed=100 + i).onset
        z = (simulated - exact) / math.sqrt(exact * (1 - exact) / EXACT_RUNS)
        s_cell = "—" if group == 1 else f"{s_rate}"
        lines.append(f"| {'seeded' if group == 1 else 'spontaneous'} | {s_cell} | {start:.4f} | {r} | {b} | {exact:.4f} | {simulated:.4f} | {z:+.2f} |")
    return lines + [""]


def scale_sweep() -> tuple[list[int], dict[int, list[float]]]:
    sizes = [2, 3, 4, 6, 8, 12, 16, 24, 32]
    curves = {g: [estimate(LoopParams(n=n, **FAST, **ILLUSTRATIVE), g, SWEEP_RUNS, seed=n).onset for n in sizes] for g in (1, 2)}
    return sizes, curves


def duration_sweep(n: int = 8) -> tuple[list[float], dict[int, list[float]]]:
    spans = [0.2, 0.5, 1, 2, 5, 10, 20, 50]
    curves = {g: [estimate(LoopParams(n=n, duration=d, rho=1.0, **ILLUSTRATIVE), g, SWEEP_RUNS, seed=int(d * 10)).onset for d in spans] for g in (1, 2)}
    return spans, curves


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    lines = ["# Loop model: sanity checks", ""] + exact_checks()

    sizes, scale = scale_sweep()
    fig, ax = plt.subplots(figsize=(6, 4))
    for g, color in ((1, "C0"), (2, "C1")):
        ax.plot(sizes, scale[g], "o-", color=color, ms=4, label=("seeded chain" if g == 1 else "spontaneous start") + " (simulation)")
    product = [start_probability(n, ILLUSTRATIVE["s"], FAST["duration"], 2) * scale[1][i] for i, n in enumerate(sizes)]
    ax.plot(sizes, product, "--", color="C1", lw=1, label="S(N) x seeded")
    ax.set(xscale="log", xlabel="number of agents $N$", ylabel="$P$(onset)")
    ax.set_xticks(sizes, [str(n) for n in sizes], fontsize=7)
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "loop_scale.png", dpi=150)

    spans, duration = duration_sweep()
    fig, ax = plt.subplots(figsize=(6, 4))
    for g, color in ((1, "C0"), (2, "C1")):
        ax.plot(spans, duration[g], "o-", color=color, ms=4, label="seeded chain" if g == 1 else "spontaneous start")
    ax.set(xscale="log", xlabel=r"duration $\rho D$", ylabel="$P$(onset)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "loop_duration.png", dpi=150)

    lines += ["## Scale sweep", "", f"Parameters: {ILLUSTRATIVE}, {SWEEP_RUNS} runs per point. A seeded chain gives the closure probability L(N);",
              "in the fast-encounter limit a spontaneous start should equal S(N) x L(N).", "",
              "| N | S(N) | seeded = L(N) | spontaneous | S(N) x L(N) |", "|---|---|---|---|---|"]
    for i, n in enumerate(sizes):
        start = start_probability(n, ILLUSTRATIVE["s"], FAST["duration"], 2)
        lines.append(f"| {n} | {start:.3f} | {scale[1][i]:.3f} | {scale[2][i]:.3f} | {start * scale[1][i]:.3f} |")
    lines += ["", "## Duration sweep (N = 8)", "", "| rho * D | seeded | spontaneous |", "|---|---|---|"]
    lines += [f"| {d} | {duration[1][i]:.3f} | {duration[2][i]:.3f} |" for i, d in enumerate(spans)]
    (RESULTS / "loop_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
