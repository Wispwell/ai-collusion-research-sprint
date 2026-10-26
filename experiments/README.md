# Experiments

Each version has a design and, when it was written before the version ran, its predictions. A version that couldn't measure anything was replaced by the next one.

| Version | Design | Predictions | Outcome |
|---|---|---|---|
| [v1](v1/DESIGN.md) | messages as files to open; start conditions with an empty channel | written before it ran | invalid: agents never opened a message file |
| [v2](v2/DESIGN.md) | messages visible in the listing; data owned by other agents | none (exploratory pilot) | no reactions without a reason to react |
| [v3](v3/DESIGN.md) | free vs blocked task × stranger / offer / reply | written before it ran | [results](v3/RESULTS.md): only a blocked agent answering a reply to its own request reacts (21/30); everything else 0/30 |
| [v4](v4/DESIGN.md) | v3's key conditions + an addressed offer, on four model families | written before it ran | replication |
