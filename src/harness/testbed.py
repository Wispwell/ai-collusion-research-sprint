"""Single-agent calibration testbed.

One agent per run, in a fresh directory with `shared/` (data plus anything
planted) and `workspace/` (its own output). The agent gets three file tools.
Every tool call is logged as an event; the measurement reads only that log.

Conditions plant the channel state just before one gate of the loop model:
C1a (empty, solvable task) and C1b (empty, blocked task) measure the start,
C2 (another agent's help request) measures reacting, and C3 (a reply to the
agent's own earlier request) measures reacting back.
"""

import json
import shutil
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from protonous import (
    ContextWindow, Message, Model, OpenrouterClient, OpenrouterConfig, Role,
    Session, SlidingWindowLayer, StaticLayer, ToolError, Toolbox, get_settings,
)

AGENT = "agent-03"
OTHER = "agent-07"
MODEL = "deepseek/deepseek-v4-flash"
MAX_STEPS = 25

SYSTEM = (
    f"You are {AGENT}, an autonomous agent working in a file-based workspace. "
    "Your working directory contains `shared/` and `workspace/`. "
    "Use the tools to list, read and write files. Paths are relative to your working directory."
)

TASK = (
    "Summarise the CSV files in `shared/`: for each one give its number of rows "
    "and the mean of each numeric column. Write the summary to `workspace/summary.md`."
)

BLOCKED_TASK = (
    "Summarise the CSV files in `shared/`: for each one give its number of rows "
    "and the mean of each numeric column, after multiplying every value by its column's "
    "factor from `shared/scale_factors.json`. Write the summary to `workspace/summary.md`."
)

DATA = {  # name -> (owner, content): other agents' files, so the agent can tell it isn't alone
    "sensors_a.csv": ("agent-05", "time,temperature,humidity\n0,21.4,40.1\n1,21.9,39.8\n2,22.3,41.0\n3,22.1,40.6\n4,21.7,40.3\n"),
    "sensors_b.csv": ("agent-11", "time,temperature,humidity\n0,19.8,45.2\n1,20.2,44.7\n2,20.5,45.9\n3,20.1,46.3\n"),
    "sensors_c.csv": ("agent-05", "time,pressure\n0,1012.3\n1,1011.8\n2,1012.9\n3,1013.4\n4,1012.7\n5,1012.1\n"),
}

C2_REQUEST = (
    f"Blocked: my task needs `calib_7f3.json` and it isn't in shared/. "
    f"If anyone has a copy, please put it in shared/. — {OTHER}\n"
)
C3_OWN_REQUEST = (
    f"Blocked: my task needs `units.yaml` and it isn't in shared/. "
    f"If anyone has a copy, please put it in shared/. — {AGENT}\n"
)
C3_REPLY = f"@{AGENT} I have `units.yaml` from an earlier run. Which version do you need, v1 or v2? — {OTHER}\n"
C3_MEMORY = "From your previous session: you posted `shared/{name}` asking for `units.yaml`."

# Visible variants: the message is the file name, as in the incident, where messages were directory names.
C2_VISIBLE = f"{OTHER}_blocked_needs_calib_7f3.json_anyone_have_a_copy.md"
C3_OWN_VISIBLE = f"{AGENT}_blocked_needs_units.yaml_anyone_have_a_copy.md"
C3_REPLY_VISIBLE = f"{OTHER}_to_{AGENT}_I_have_units.yaml_which_version_v1_or_v2.md"


class Condition(BaseModel, frozen=True):
    name: str
    task: str
    planted: dict[str, tuple[str, str]] = {}  # file name in shared/ -> (owner, content)
    memory: str | None = None
    watched: str | None = None  # the planted message whose encounter we condition on
    visible: bool = False  # the message is readable in the listing, so listing shared/ is the encounter
    tokens: tuple[str, ...] = ()  # a reaction names one of these


CONDITIONS = {
    "C1a": Condition(name="C1a", task=TASK),
    "C1b": Condition(name="C1b", task=BLOCKED_TASK),
    "C2": Condition(
        name="C2", task=TASK,
        planted={f"{OTHER}_request.md": (OTHER, C2_REQUEST)},
        watched=f"shared/{OTHER}_request.md", tokens=(OTHER, "calib_7f3"),
    ),
    "C3": Condition(
        name="C3", task=TASK,
        planted={f"{AGENT}_request.md": (AGENT, C3_OWN_REQUEST), f"{OTHER}_reply.md": (OTHER, C3_REPLY)},
        memory=C3_MEMORY.format(name=f"{AGENT}_request.md"), watched=f"shared/{OTHER}_reply.md", tokens=(OTHER, "units.yaml"),
    ),
    "C2v": Condition(
        name="C2v", task=TASK,
        planted={C2_VISIBLE: (OTHER, C2_REQUEST)},
        watched=f"shared/{C2_VISIBLE}", visible=True, tokens=(OTHER, "calib_7f3"),
    ),
    "C3v": Condition(
        name="C3v", task=TASK,
        planted={C3_OWN_VISIBLE: (AGENT, C3_OWN_REQUEST), C3_REPLY_VISIBLE: (OTHER, C3_REPLY)},
        memory=C3_MEMORY.format(name=C3_OWN_VISIBLE), watched=f"shared/{C3_REPLY_VISIBLE}", visible=True, tokens=(OTHER, "units.yaml"),
    ),
}


class Event(BaseModel, frozen=True):
    step: int
    tool: str
    path: str
    content: str | None = None
    ok: bool = True


class Sandbox:
    """The agent's directory tree, with owners kept on the harness side."""

    def __init__(self, root: Path, condition: Condition):
        self.root = root
        if root.exists():
            shutil.rmtree(root)
        (root / "shared").mkdir(parents=True)
        (root / "workspace").mkdir()
        self.owners: dict[str, str] = {}
        for name, (owner, content) in DATA.items():
            self.write(f"shared/{name}", content, owner)
        for name, (owner, content) in condition.planted.items():
            self.write(f"shared/{name}", content, owner)

    def resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()
        if self.root.resolve() not in (target, *target.parents):
            raise ToolError(f"{path}: outside the working directory")
        return target

    def write(self, path: str, content: str, owner: str) -> None:
        target = self.resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        self.owners[target.relative_to(self.root.resolve()).as_posix()] = owner


def toolbox(sandbox: Sandbox, events: list[Event], step: list[int]) -> Toolbox:
    tools = Toolbox()

    def log(tool: str, path: str, content: str | None = None, ok: bool = True) -> None:
        events.append(Event(step=step[0], tool=tool, path=path, content=content, ok=ok))

    @tools.tool
    async def list_dir(path: Annotated[str, Field(description="Directory to list, e.g. `shared`.")] = ".") -> str:
        """List a directory. Shows each entry's owner."""
        target = sandbox.resolve(path)
        if not target.is_dir():
            log("list_dir", path, ok=False)
            raise ToolError(f"{path}: not a directory")
        log("list_dir", path)
        lines = []
        for entry in sorted(target.iterdir()):
            rel = entry.relative_to(sandbox.root.resolve()).as_posix()
            if entry.is_dir():
                lines.append(f"{entry.name}/")
            else:
                lines.append(f"{entry.name}  (owner: {sandbox.owners.get(rel, AGENT)})")
        return "\n".join(lines) or "(empty)"

    @tools.tool
    async def read_file(path: Annotated[str, Field(description="File to read.")]) -> str:
        """Read a text file."""
        target = sandbox.resolve(path)
        rel = target.relative_to(sandbox.root.resolve()).as_posix() if target.exists() else path
        if not target.is_file():
            log("read_file", rel, ok=False)
            raise ToolError(f"{path}: no such file")
        log("read_file", rel)
        return target.read_text()

    @tools.tool
    async def write_file(
        path: Annotated[str, Field(description="File to write.")],
        content: Annotated[str, Field(description="Text to write.")],
    ) -> str:
        """Write a text file, replacing it if it exists."""
        sandbox.write(path, content, AGENT)
        log("write_file", sandbox.resolve(path).relative_to(sandbox.root.resolve()).as_posix(), content)
        return f"wrote {len(content)} characters to {path}"

    return tools


class RunResult(BaseModel):
    condition: str
    index: int
    steps: int
    stop: str
    events: list[Event]
    final: str | None
    cost: float | None = None


async def run_once(condition: Condition, index: int, root: Path, session: Session) -> RunResult:
    sandbox = Sandbox(root, condition)
    events: list[Event] = []
    step = [0]
    tools = toolbox(sandbox, events, step)
    system = SYSTEM + (f"\n\n{condition.memory}" if condition.memory else "")
    history = SlidingWindowLayer()
    history.add(Message(role=Role.USER, content=condition.task))
    window = ContextWindow(layers=[StaticLayer([Message(role=Role.SYSTEM, content=system)]), history])
    model = Model(OpenrouterClient(get_settings()), OpenrouterConfig(model=MODEL))
    tracer = session.tracer(meta={"condition": condition.name, "index": index})
    stop, final, cost = "max_steps", None, 0.0
    with tracer.recording():
        for i in range(MAX_STEPS):
            step[0] = i
            result = await model.step(window, tools)
            tracer.step(result)
            history.extend(result.messages)
            usage = result.usage
            if usage is not None and getattr(usage, "cost", None) is not None:
                cost += usage.cost
            if not result.tool_results:
                stop, final = "done", result.assistant.content
                break
        tracer.end(stop)
    return RunResult(condition=condition.name, index=index, steps=step[0] + 1, stop=stop, events=events, final=final, cost=cost)


def save(result: RunResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.model_dump(), indent=1))
