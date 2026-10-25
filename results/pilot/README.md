# Pilot runs

Run after the predictions were pushed (commit 6901ffc) and before the main batch.
They informed the redesign recorded in the amendment to `PREDICTIONS.md`.

- `v1/`: planted messages as files to open; data files owned by `system`.
  `C2/run-90-pre-fix.json` is the first run, with data in `shared/data/`: the agent
  went straight to the subdirectory and never listed `shared/`, so the data was
  moved up into `shared/`.
  Result: agents listed `shared/` but never opened a planted message (0/4 in C2, C3).
  Blocked agents (C1b) reported the missing file to the user, not to the channel.
- `v2/`: data files owned by other agents (`agent-05`, `agent-11`); in C2v/C3v the
  message is the file name, visible in the listing.
  Result: no writes into `shared/` in any of 8 runs, including C3v, where the listing
  shows a reply addressed to the agent by name.

The harness at this commit is the v2 harness.
