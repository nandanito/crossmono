# Contributing to CrossMono

Thank you for helping. CrossMono is a small project with one maintainer, so a short note before a big change
saves everyone time.

## What belongs here

CrossMono is CrossPoint Reader for the M5Stack PaperMono and PaperMono-Lite, plus the PaperMono hardware that
CrossPoint does not use. See [docs/roadmap.md](docs/roadmap.md) for what is planned and
[docs/decisions/](docs/decisions/README.md) for the decisions behind it.

- **A change that helps every CrossPoint device** (the reader, the interface, formats, fonts, the web tools)
  belongs in [CrossPoint](https://github.com/crosspoint-reader/crosspoint-reader). Read its `SCOPE.md` and its
  [contributing docs](docs/contributing/README.md). When CrossMono needs such a fix early, we carry it only until
  it lands in CrossPoint.
- **Drivers and board support** belong in the [FreeInk SDK](https://github.com/Free-Ink/freeink-sdk). New drivers
  can start here in `lib/mono-*`, in the SDK's style, and move to the SDK once stable.
- **PaperMono features, CrossMono's install, updates, releases and branding** belong here.

For anything bigger than a small fix, open an [issue](https://github.com/nandanito/crossmono/issues) or a
[discussion](https://github.com/nandanito/crossmono/discussions) first. A change to a decision needs a new decision
record, not an edit of the old one ([docs/decisions/README.md](docs/decisions/README.md)).

## How the repository is shared with CrossPoint

CrossMono's `main` branch shares its history with CrossPoint, and CrossPoint's releases are merged in
([docs/upstream-sync.md](docs/upstream-sync.md)). To keep those merges simple:

- **CrossMono's own files** are `src/mono/`, `lib/mono-*`, `scripts/mono/`, `test/mono/`,
  `partitions_papermono.csv`, `.github/README.md`, the CrossMono documents (`docs/decisions/`, `docs/roadmap.md`,
  `docs/upstream-sync.md`, `docs/install.md`, `docs/hardware-test-checklist.md`, `VERSIONING.md`, `RELEASING.md`,
  `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `THIRD-PARTY-NOTICES`). Put new code there when you can.
- **Everything else is CrossPoint's**, including the root `README.md`, `USER_GUIDE.md`, `SCOPE.md` and
  `ROADMAP.md`. Edit those files only when there is no other way. Keep the edit small and add or update its row in
  the seams table in [docs/upstream-sync.md](docs/upstream-sync.md) in the same pull request.
- **Never delete a CrossPoint file.** Features are turned off with build flags instead
  ([ADR 0006](docs/decisions/0006-stripping.md)).
- `freeink-sdk/` is a submodule at the commit CrossPoint pins. Do not move it in a pull request.

## Build and test

Set up the tools as in CrossPoint's [getting started guide](docs/contributing/getting-started.md) (pioarduino
PlatformIO Core, Python 3, clang-format 21), then:

```sh
git clone --recursive https://github.com/nandanito/crossmono.git
cd crossmono
pio run -e papermono                    # development build
pio run -e papermono-gh_release         # release build
pio run -t unit-tests                   # host tests
python3 scripts/mono/size_gate.py --env papermono-gh_release   # flash-size check, after the release build
bin/clang-format-fix                    # format the code
pio run -e papermono -t upload          # flash a connected device (keeps its internal memory)
```

CI runs the same checks on every pull request.

The code rules are CrossPoint's: [AGENTS.md](AGENTS.md) and the files in `.agents/rules/` (memory and allocation,
hardware access, coding style, translations). Where [CLAUDE.md](CLAUDE.md) differs, CLAUDE.md applies in this
repository. New user-facing text goes into `lib/I18n/translations/english.yaml` as new keys; other languages fall
back to English.

## Pull requests

- Branch from `main` and open the pull request against `main`.
- Use a semantic title: `feat:`, `fix:`, `docs:`, `chore:` and so on.
- Say what you tested. For firmware changes, list what to check on the device and on which model. A firmware pull
  request is merged only after a test on a real device.
- Pull requests are merged with a merge commit. Please do not rebase `main`.
- If you used AI tools, you are still responsible for every line: read it, test it, and be ready to explain it.

Contributions are accepted under the [MIT licence](LICENSE) of this repository.

## Testers

Testing on a device helps as much as code, and the **PaperMono-Lite** has not been tested by us yet. Install a
release or a test build ([docs/install.md](docs/install.md)) and report what works and what does not.

---

CrossMono is independent community firmware. It is not affiliated with or supported by M5Stack. PaperMono is a
product of M5Stack.
