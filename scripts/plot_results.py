"""Plot reaction rates per condition and model (v3 and v4), with 95% Wilson intervals.

    PYTHONPATH=src:scripts python scripts/plot_results.py

Writes results/figures/reactions.png.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

from harness.testbed import CONDITIONS
from analyze_calibration import any_message, measure, wilson

ROOT = Path(__file__).resolve().parent.parent
V3 = ROOT / "experiments" / "v3" / "results" / "logs"
V4 = ROOT / "experiments" / "v4" / "results" / "logs"
FIGURE = ROOT / "results" / "figures" / "reactions.png"

ORDER = ["blocked-offer", "blocked-addressed", "blocked-reply"]
MODELS = {
    "deepseek/deepseek-v4-flash": "DeepSeek-V4-Flash",
    "anthropic/claude-sonnet-5.5": "Claude Sonnet 5.5",
    "openai/gpt-5.6-terra": "GPT-5.6 Terra",
    "google/gemini-3.8-flash": "Gemini 3.8 Flash",
}


def rate(directory: Path, condition: str) -> tuple[int, int, int]:
    seen = reacted = broad = 0
    for f in sorted((directory / condition).glob("run-*.json")):
        run = json.loads(f.read_text())
        s, r, _ = measure(run, CONDITIONS[condition].tokens)
        seen += s
        reacted += r
        broad += any_message(run)
    return reacted, seen, broad


def main() -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    width = 0.2
    for i, (model, label) in enumerate(MODELS.items()):
        xs, ys, lows, highs = [], [], [], []
        for j, condition in enumerate(ORDER):
            source = V3 if model == "deepseek/deepseek-v4-flash" and condition != "blocked-addressed" else V4 / model.replace("/", "__")
            k, n, wide = rate(source, condition)
            if n == 0:
                continue
            if wide != k:
                ax.plot(j + (i - 1.5) * width, wide / n, marker="o", mfc="none", mec="black", ms=6, zorder=3)
            lo, hi = wilson(k, n)
            xs.append(j + (i - 1.5) * width)
            ys.append(k / n)
            lows.append(k / n - lo)
            highs.append(hi - k / n)
        ax.bar(xs, ys, width, yerr=[lows, highs], capsize=2, label=label)
    ax.set_xticks(range(len(ORDER)), ["offer,\nnot addressed", "offer,\naddressed by name", "reply to its\nown request"])
    ax.set_ylabel("share of runs that reacted")
    ax.set_ylim(0, 1.05)
    ax.plot([], [], marker="o", mfc="none", mec="black", ls="none", label="secondary rule, where it differs")
    ax.legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22), frameon=False)
    fig.tight_layout()
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=200)


if __name__ == "__main__":
    main()
