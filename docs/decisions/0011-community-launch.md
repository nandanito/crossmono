# 0011. Community launch

- Status: Accepted
- Date: 2026-10-28

## Context

CrossMono is meant for strangers from the first release, not only for its author. CrossPoint is MIT
(`LICENSE`: "Copyright (c) 2025 CrossPoint Reader organization"). The FreeInk SDK is MIT (© 2026 FreeInk); its
NOTICE lists OpenX4 (MIT) and the Bosch BMI270 configuration blob (BSD-3-Clause). CrossPoint welcomes downstream
forks and lists them in its README (`README.md:282-288`). Its `AGENTS.md` requires that a human writes PR
descriptions for CrossPoint.

## Options considered

1. **Quiet start, announce at 1.0.** Less support load, but no testers, and no Lite tester in particular.
2. **Announce from the first release candidate, with clear "pre-1.0" wording** (chosen). Finds testers early;
   needs the README and install docs to be good from the start.

## Decision

- Licence: MIT. Upstream's `LICENSE` text is kept, and our copyright line is added below theirs.
- `THIRD-PARTY-NOTICES` lists bundled third-party code and its licences (FreeInk SDK, OpenX4, Bosch BMI270 blob,
  CrossPlay stack-budget script, and later RadioLib and M5Unit-NFC).
- Files for strangers: a README written for people who have never heard of CrossPoint, `CONTRIBUTING`, issue
  templates and `SECURITY`.
- Channels:
  - M5Stack: the community forum, a request to be listed in the PaperMono docs, and direct contact with M5Stack.
  - CrossPoint community: Discord, and a PR adding CrossMono to the README's "Community forks" list.
  - Reddit: r/eink, r/esp32, r/M5Stack.
  - X, Bluesky and Mastodon.
  - Show HN at the first stable release.
- Every announcement uses the wording from [0002](0002-identity-and-scope.md).

## Consequences

- README, `LICENSE`, `.github/ISSUE_TEMPLATE/*` and `.github/PULL_REQUEST_TEMPLATE.md` become seams in 0.1.0.
- Text for other projects (the CrossPoint "Community forks" PR, SDK PRs, forum posts) is short and plain, and is
  written or approved by Nandan before it is posted.
- Asking for a PaperMono-Lite tester is part of the first announcement ([0003](0003-two-models.md)).

## Sources

- `LICENSE`, `README.md:282-288`, `AGENTS.md` ("Human ownership") at `60d3c8bb`
- `freeink-sdk/LICENSE`, `freeink-sdk/NOTICE` at `a5d5332`
- https://community.m5stack.com, https://www.reddit.com/r/eink/, https://www.reddit.com/r/esp32/,
  https://www.reddit.com/r/M5Stack/, https://news.ycombinator.com/showhn.html
