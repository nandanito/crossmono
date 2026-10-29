# CrossMono decision records

Each project-level decision is recorded once, here, as a short decision record (ADR). A record is not rewritten
when plans change: a later record replaces it, and the old one gets the status `Superseded by NNNN`.

Line references (`path:line`) point at the bootstrap base unless a record says otherwise:

- CrossPoint Reader `60d3c8bb` (`develop`, 2026-10-28), the first commit on our `main`
- FreeInk SDK `a5d5332`, the submodule commit pinned by that base

Paths under `freeink-sdk/` are inside the submodule.

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-repo-and-upstream.md) | Repository and upstream | Accepted |
| [0002](0002-identity-and-scope.md) | Identity and scope | Accepted |
| [0003](0003-two-models.md) | PaperMono and PaperMono-Lite: one build | Accepted |
| [0004](0004-versioning.md) | Versioning | Accepted |
| [0005](0005-partitions.md) | Partition table | Accepted |
| [0006](0006-stripping.md) | Removing upstream features | Accepted |
| [0007](0007-ui.md) | User interface | Accepted |
| [0008](0008-hardware-features.md) | Hardware features | Accepted |
| [0009](0009-install.md) | Install and update | Accepted |
| [0010](0010-quality-and-ci.md) | Quality and CI | Accepted |
| [0011](0011-community-launch.md) | Community launch | Accepted |

## Template

Copy this into `NNNN-short-title.md` with the next free number, and add a row to the index.

```markdown
# NNNN. Title

- Status: Proposed | Accepted | Superseded by NNNN
- Date: YYYY-MM-DD

## Context

The problem, and the facts that limit the answer. Cite files as `path:line` and give URLs.

## Options considered

Each option with its main cost and benefit.

## Decision

What we do. Short enough to check against the code later.

## Consequences

What gets easier, what gets harder, and the follow-up work this creates.

## Sources

The files, links and measurements this record relies on.
```
