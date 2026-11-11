# 0015. The SDK pin may move ahead of a CrossPoint release for a needed fix

- Status: Accepted
- Date: 2026-11-11

Line references are at `main` `fb9054bd` (CrossPoint base `42d58daa`, 2.0.0) and, under `freeink-sdk/`, at the old
pin `5e94fe7` unless a line says `6a208c0`.

## Context

[ADR 0008](0008-hardware-features.md) says we do not move the FreeInk SDK submodule ourselves: we use the pin that
upstream ships, and it changes when we merge a CrossPoint release ([upstream-sync.md](../upstream-sync.md)).
CLAUDE.md says the same. At CrossPoint 2.0.0 the pin is `5e94fe7`.

**Updates over Wi-Fi are broken on that pin.** In the 0.2.0-rc.1 hardware checklist (2026-11-11), a build of the
`0.1.0` source pointed at the `0.2.0-rc.1` release found the update and then failed the download: `wolfSSL request
failed: status -1` on `https://github.com/nandanito/crossmono/releases/download/0.2.0-rc.1/…`, right after the TLS
handshake, twice. GitHub answers that URL with a 302 whose `Content-Security-Policy` line is 4,174 bytes long
(HTTP/1.1, measured with curl the same day). The SDK's header reader stops at `MAX_LINE = 4096` bytes and gives up
the response (`freeink-sdk/libs/network/SecureNet/include/SecureHttpClient.h:251-260, 535-550, 622`). The update
from `0.1.0-rc.1` to `0.1.0` worked on 2026-11-07, so GitHub's header grew after that. Every build on `5e94fe7`,
0.1.0 and 0.2.0-rc.1 included, cannot update over Wi-Fi now. Other downloads from GitHub fail the same way;
CrossPoint names font downloads (#4420).

**The SDK has the fix, CrossPoint `develop` pins it, no release has it.** FreeInk SDK `6a208c0` (2026-11-10, "skip
oversized GitHub CSP response headers") skips a `Content-Security-Policy` line that is too long and keeps the other
limits (8,192 bytes of headers in all). CrossPoint `develop` pins `6a208c0` since #4420 ("update FreeInk SDK for font
downloads", `ddd3b1d8`). CrossPoint's latest release is still 2.0.0, and nothing says when the next one comes.

`5e94fe7..6a208c0` is 47 commits. For the PaperMono they bring the touch bring-up fix (`1e1cec2`, our PR #168),
the request-replay fix (`9ded431`, our PR #171), BLE page-turner reconnect fixes (`8057702`, `a8db7d3`) and the
header fix. The rest is for other boards (EEGO A4, Picco, Murphy, X3, Metalio) or reports SD usage. CrossPoint's
own code needed no change for the two pin moves after 2.0.0 (#4392, #4420 change only the submodule).

## Options considered

1. **Wait for the next CrossPoint release and sync.** No new rule, but 0.2.0 waits for an unknown date, and every
   build until then cannot update over Wi-Fi.
2. **Work around it in the updater.** Download through the API asset URL
   (`api.github.com/repos/…/releases/assets/<id>` with `Accept: application/octet-stream`), whose answer has short
   headers (2,030 bytes in all, longest line 958). It keeps the pin, but it edits `lib/JsonParser` (upstream) and
   the updater, other GitHub downloads stay broken, and the code goes again at the next sync.
3. **Merge CrossPoint `develop` now.** [upstream-sync.md](../upstream-sync.md) allows a merge between releases for
   a fix we need. But it also brings develop's unreleased features (SD usage in About, the reordered Controls
   settings, rotation fixes) into a release candidate, and puts a non-release base into About.
4. **Move the pin to the commit CrossPoint `develop` pins.** No CrossMono code, fixes every GitHub download, and the
   next sync lands on the same pin or a later one. It departs from ADR 0008's rule.

## Decision

Option 4, under this rule, which replaces ADR 0008's "SDK pin" bullet and the matching CLAUDE.md line:

- The SDK pin is the one our CrossPoint base ships, unless a release needs a fix that the base's pin lacks. Then
  the pin may move to the commit that CrossPoint `develop` pins, and only to that commit. Never to an SDK commit
  that CrossPoint does not pin.
- A move is recorded in a decision record or an addendum to this one, in the CHANGELOG's Upstream block and in
  [upstream-sync.md](../upstream-sync.md). It goes through the full firmware handoff and the hardware checklist.
- At the next sync the pin is CrossPoint's again. If CrossPoint's release pins an older commit than ours, we keep
  ours and say so in the sync PR.

For 0.2.0: the pin moves from `5e94fe7` to `6a208c0`, and 0.2.0 gets a second candidate, `0.2.0-rc.2`.

## Consequences

- Updates over Wi-Fi work again from 0.2.0 on. Devices on 0.1.0 or 0.2.0-rc.1 cannot get the fix over Wi-Fi: their
  updater fails before it downloads anything, so they need a USB install. The release notes and the install docs
  must say so.
- About shows `FreeInk SDK 6a208c0` with CrossPoint base 2.0.0, a combination CrossPoint never released. The
  hardware checklist runs in full on it (touch after wake, BLE page turners, updates, downloads).
- The touch bring-up carry (`mono::beginInput`, `src/main.cpp`) is no longer needed, because the pin now has
  `1e1cec2`. It stays in 0.2.0, so the change is the pin only; it goes at the next sync as planned. Both waits can
  run on a slow boot; each is bounded.
- The fix allows 8,192 bytes of response headers in all. GitHub's 302 has about 5.7 KB now; if it grows past the
  budget, the updater fails again, and the fix belongs in the SDK.

## Sources

- Serial log of the 0.2.0-rc.1 checklist run, 2026-11-11 21:19-21:20 (`[OTA]`, `[HTTP]` lines), and the record in
  the 0.2.0 release PR.
- `curl --http1.1 -I` on the release download URL and on the API asset URL, 2026-11-11.
- `freeink-sdk` `6a208c0` (`libs/network/SecureNet/include/SecureHttpClient.h`), `git -C freeink-sdk log
  5e94fe7..6a208c0`.
- CrossPoint `develop` `ddd3b1d8` (#4420), `7a67cddb` (#4392), `5d731041` (#4331).
