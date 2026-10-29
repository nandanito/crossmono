# 0001. Repository and upstream

- Status: Accepted
- Date: 2026-10-28

## Context

CrossMono is firmware for the M5Stack PaperMono built on CrossPoint Reader. CrossPoint is MIT licensed, its default
branch is `develop`, and it has about 8.5k stars and 2.1k forks. At planning time the newest releases were `2.0.0rc`
(pre-release, 2026-10-19) and `1.6.5` (stable, 2026-09-27). `develop` was already past `2.0.0rc` with memory and
performance fixes.

CrossPoint welcomes downstream forks (`SCOPE.md:61-73`) and lists community forks in its README
(`README.md:282-288`). We want to follow upstream closely, keep our own diff small and easy to review, and be
public from the first day.

## Options considered

1. **GitHub fork of `crosspoint-reader/crosspoint-reader`.** One click, and GitHub shows "forked from". But the
   repository stays inside CrossPoint's fork network: GitHub repository search hides forks by default, and the
   pull-request UI defaults the base repository to the parent, so a PR meant for us can be opened against
   CrossPoint by mistake.
2. **New repository with CrossPoint's full history imported.** A normal, searchable repository with its own
   default branch and issues. Full history keeps `git blame`, and upstream updates are ordinary merges. We lose
   the automatic "forked from" link, so the README credits CrossPoint by hand.
3. **New repository from a snapshot without history.** Simplest start, but every upstream update becomes a hand
   made patch and blame is lost. Rejected.

For the base commit: the `1.6.5` stable tag is behind on the 2.0 work; the `2.0.0rc` tag misses the fixes made
after it; `develop` has them, and `2.0.0` is expected soon.

## Decision

- New repository `nandanito/crossmono`, public, with CrossPoint's full history imported (option 2). Not a GitHub
  fork.
- `main` starts at CrossPoint `develop` as fetched on 2026-10-29. When CrossPoint tags `2.0.0`, we merge that tag.
- Later, we merge upstream at each upstream release: branch `sync/crosspoint-<version>` → PR → merge commit. The
  procedure is in [docs/upstream-sync.md](../upstream-sync.md).
- Our code lives in new files: `src/mono/`, `lib/mono-*`, and our own docs (`docs/decisions/`, `docs/roadmap.md`,
  `docs/upstream-sync.md`, `docs/hardware-test-checklist.md`, `VERSIONING.md`, `RELEASING.md`). Every upstream file
  we edit is listed in the seams table in [docs/upstream-sync.md](../upstream-sync.md) and checked after every
  sync.

### Bootstrap record (2026-10-29)

| Item | Value |
|---|---|
| Upstream base | `60d3c8bbd35b957c0c2c5075928a38b5ed1608cd` on `develop` (committed 2026-10-28, "fix: Scale custom covers up & let you set them on touch boards (#4185)") |
| Distance from `2.0.0rc` | 64 commits after the tag |
| Upstream version string | `[crosspoint] version = 2.0.0` (`platformio.ini:6-7`) |
| FreeInk SDK pin | `a5d5332e82502198ad1bc5a6236eca57afab39d9` (moved from `44427f8` in the base commit itself) |
| Dropped | The empty "Initial commit" `9adfc9e`; `main` now starts at the upstream base |
| Remotes | `origin` = `nandanito/crossmono`; `upstream` = CrossPoint, fetch only (push URL set to `DISABLED`), upstream tags fetched as `refs/tags/upstream/*` |

## Consequences

- `main` shares history with CrossPoint `develop`, so it must never be rebased or squashed. PRs into `main` are
  merged with a merge commit.
- Upstream files come along unchanged, including `README.md`, `SCOPE.md`, `ROADMAP.md`, `AGENTS.md` and
  `.github/workflows/*`. Until the 0.1.0 work replaces them, the repository front page still reads like
  CrossPoint, and the inherited `ci.yml` runs on our pull requests (its push trigger is limited to `develop`).
- Our roadmap is `docs/roadmap.md`, because upstream already owns the root `ROADMAP.md`.
- `CLAUDE.md` was a symlink to upstream's `AGENTS.md`. It is now a real file that imports `AGENTS.md` and then
  adds the CrossMono rules. This is the first entry in the seams table.
- A `git fetch upstream` brings upstream tags in under `upstream/`, so they never mix with our own release tags.

## Sources

- https://github.com/crosspoint-reader/crosspoint-reader (licence, default branch, releases)
- `SCOPE.md:61-73` (CrossPoint as a downstream foundation), `README.md:282-288` (community forks)
- `platformio.ini:6-7`, `.gitmodules`, `git log -p -- freeink-sdk` at `60d3c8bb`
- `.github/workflows/ci.yml` (triggers: push to `develop`, any pull request)
- GitHub docs, searching for repositories (forks are not shown unless asked for):
  https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories
