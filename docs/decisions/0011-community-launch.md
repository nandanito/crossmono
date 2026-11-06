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

## Addendum 2026-11-05: licence of the image, README and community files

Facts and choices from the 0.1.0 documentation work (Nandan, 2026-11-05). The decision stands; these details
replace parts of the Decision and Consequences where they differ.

- **The firmware image is GPLv3 as a whole.** The image includes wolfSSL 5.7.2 (Arduino-wolfSSL, "GPLv2 (or at
  your option any later version)", its `LICENSING` file). CrossPoint's `develop` after 2.0.0 says the same for its
  firmware: "The combined firmware executable uses GPLv3 because it includes wolfSSL" (`LICENSE` and
  `licenses/README.md`, crosspoint-reader#4064, `136c2655`). The code stays MIT: `LICENSE` keeps upstream's text
  with our copyright line below it. The README says both.
- **`THIRD-PARTY-NOTICES` lists every bundled component**, not only the FreeInk SDK, OpenX4 and the BMI270 blob:
  the libraries, the platform, CrossPoint's third-party code, fonts and data, and the SDK parts, each with its
  licence and where the licence text is, plus how to get the source of a release. It was checked against the 2.0.0
  base and the `papermono-gh_release` libraries. The CrossPlay stack-budget script gets its entry when the script
  is added (0.1.0 plan, PR 10). When a sync brings CrossPoint's own `licenses/` folder, our file points at it and
  keeps only what CrossMono adds.
- **Not done in 0.1.0:** release assets carry no licence file. CrossPoint's `develop` attaches a generated
  `LICENSE` (`scripts/build_release_license.py`); decide at the sync that brings it whether to do the same.
- **README:** ours is `.github/README.md`, which GitHub shows before the root `README.md` (GitHub Docs, "About
  READMEs"). The root `README.md` stays CrossPoint's, with a short note at the top that points at ours. This
  replaces the "README becomes a seam" bullet: only that note is a seam, so CrossPoint's frequent README changes
  (14 commits in the four months before this addendum) merge without conflicts.
- **USER_GUIDE.md** stays CrossPoint's, unchanged. Our README lists what differs on CrossMono.
- **SECURITY.md** asks for reports through GitHub's private vulnerability reporting, turned on for
  `nandanito/crossmono` on 2026-11-05.
- **`.github/FUNDING.yml`** is kept but empty (a comment only), so GitHub no longer shows CrossPoint's sponsor link
  on our repository.

Sources: `.pio/libdeps/papermono-gh_release/Arduino-wolfSSL/LICENSING` and `library.json` (which says
"GPL-2.0-only"); `git show upstream/develop:licenses/README.md`; https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes

## Addendum 2026-11-06: the release licence file

The 2026-11-05 addendum says that release assets carry no licence file in 0.1.0. That changed before the first
release: every release has `crossmono-<version>-LICENSE.txt` with all licence texts and the source commits
([0009](0009-install.md), addendum 2026-11-06). It is written by our own `scripts/mono/release_license.py` until
the CrossPoint sync that brings CrossPoint's `scripts/build_release_license.py`. We do not copy CrossPoint's script
before that sync: it titles the file "CrossPoint Reader firmware licenses", links build steps in
`licenses/README.md` (not copied, because it describes CrossPoint's script), and its library list does not have
AnimatedGIF, which our 2.0.0 build links. `licenses/*.txt` are CrossPoint's texts, copied unchanged from
`136c2655`; `THIRD-PARTY-NOTICES` points at them.
