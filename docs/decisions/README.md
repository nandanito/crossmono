# CrossMono decision records

Each project-level decision is recorded once, here, as a short decision record (ADR). A record is not rewritten
when plans change: a later record replaces it, and the old one gets the status `Superseded by NNNN`.

Line references (`path:line`) point at the bootstrap base unless a record or an addendum says otherwise:

- CrossPoint Reader `60d3c8bb` (`develop`, 2026-10-28), the first commit on our `main`
- FreeInk SDK `a5d5332`, the submodule commit pinned by that base

Paths under `freeink-sdk/` are inside the submodule.

## Changing a record

- **A decision changes:** write a new record. The old record gets the status `Superseded by NNNN`, or names the
  part that is replaced (as 0003 does for its probe), and the index row says the same.
- **A fact is new, or a detail is settled, and the decision stands:** add a dated section at the end of the
  record, `## Addendum YYYY-MM-DD: <topic>`.
- **The record states something wrong:** add `## Erratum YYYY-MM-DD: <topic>` at the end. Say what was wrong, and
  what is true now.
- Leave the earlier text as it was written, so the record still shows what was known when it was decided. An
  addendum or erratum that cites lines at a later base says which base (or commit) it uses.

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-repo-and-upstream.md) | Repository and upstream | Accepted |
| [0002](0002-identity-and-scope.md) | Identity and scope | Accepted |
| [0003](0003-two-models.md) | PaperMono and PaperMono-Lite: one build | Accepted; probe replaced by 0012, Lite tester by 0013 |
| [0004](0004-versioning.md) | Versioning | Accepted |
| [0005](0005-partitions.md) | Partition table | Accepted |
| [0006](0006-stripping.md) | Removing upstream features | Accepted |
| [0007](0007-ui.md) | User interface | Accepted |
| [0008](0008-hardware-features.md) | Hardware features | Accepted |
| [0009](0009-install.md) | Install and update | Accepted |
| [0010](0010-quality-and-ci.md) | Quality and CI | Accepted |
| [0011](0011-community-launch.md) | Community launch | Accepted |
| [0012](0012-boot-model-probe.md) | Boot model probe | Accepted; Lite tester replaced by 0013 |
| [0013](0013-lite-untested-at-0-1-0.md) | The Lite at 0.1.0: untested, reports welcome | Accepted |

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
