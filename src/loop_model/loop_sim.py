"""Monte Carlo simulation of the loop model of coordination.

A reaction is a message written in response to another message. A turn of
coordination closes when an agent reacts to a message that descends from one
of its own messages: the influence has come back to where it started.

Agents act asynchronously. Every (agent, message) pair gets an exponential
encounter delay with rate rho, counted from the message's creation. At the
first encounter the agent decides once (one-shot):
- the message is a direct reaction to the agent's own message: react with b
- any other message by someone else: react with r
A reaction is a new message, open to reactions in turn. Agents never react to
their own messages.

Two starts: group=1 is a seeded chain (a first message from one of the agents is
in the channel at time 0); group=2 is a spontaneous start (the channel begins
empty and each agent posts first at rate s).
"""

import heapq
import itertools
import math

import numpy as np
from pydantic import BaseModel, Field


class LoopParams(BaseModel, frozen=True):
    n: int = Field(ge=2, description="number of real agents")
    duration: float = Field(gt=0, description="observation window D")
    rho: float = Field(gt=0, description="encounter rate of one agent with one message")
    s: float = Field(ge=0, description="spontaneous first-post rate per agent (group 2)")
    r: float = Field(ge=0, le=1, description="react to someone else's message")
    b: float = Field(ge=0, le=1, description="react to a direct reaction to one's own message")


class LoopOutcome(BaseModel, frozen=True):
    onset: bool
    onset_time: float
    messages: int
    truncated: bool


class LoopRates(BaseModel, frozen=True):
    runs: int
    onset: float
    truncated: float
    mean_messages: float


def run(rng: np.random.Generator, params: LoopParams, group: int, max_messages: int = 5000) -> LoopOutcome:
    """Run until the first closed loop, the end of the window, or the message cap."""
    end = params.duration
    if group == 1:
        root_time = 0.0
    else:
        rate = params.n * params.s
        root_time = rng.exponential(1 / rate) if rate > 0 else math.inf
        if root_time > end:
            return LoopOutcome(onset=False, onset_time=math.inf, messages=0, truncated=False)
    root_author = int(rng.integers(params.n))

    authors: list[int] = []
    parents: list[int | None] = []
    lineage: list[frozenset[int]] = []  # authors of the message and all its ancestors
    events: list[tuple[float, int, int, int]] = []  # (time, tie-break, agent, message)
    tie = itertools.count()

    def post(author: int, parent: int | None, time: float) -> None:
        index = len(authors)
        authors.append(author)
        parents.append(parent)
        lineage.append((lineage[parent] if parent is not None else frozenset()) | {author})
        delays = rng.exponential(1 / params.rho, params.n)
        for agent in range(params.n):
            if agent != author and time + delays[agent] <= end:
                heapq.heappush(events, (time + delays[agent], next(tie), agent, index))

    post(root_author, None, root_time)
    while events:
        if len(authors) >= max_messages:
            return LoopOutcome(onset=False, onset_time=math.inf, messages=len(authors), truncated=True)
        time, _, agent, message = heapq.heappop(events)
        parent = parents[message]
        direct = parent is not None and authors[parent] == agent
        if rng.random() >= (params.b if direct else params.r):
            continue
        if agent in lineage[message]:
            return LoopOutcome(onset=True, onset_time=time, messages=len(authors) + 1, truncated=False)
        post(agent, message, time)
    return LoopOutcome(onset=False, onset_time=math.inf, messages=len(authors), truncated=False)


def estimate(params: LoopParams, group: int, runs: int, seed: int) -> LoopRates:
    rng = np.random.default_rng(seed)
    onsets = truncated = messages = 0
    for _ in range(runs):
        outcome = run(rng, params, group)
        onsets += outcome.onset
        truncated += outcome.truncated
        messages += outcome.messages
    return LoopRates(runs=runs, onset=onsets / runs, truncated=truncated / runs, mean_messages=messages / runs)
