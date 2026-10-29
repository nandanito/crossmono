# 0002. Identity and scope

- Status: Accepted
- Date: 2026-10-28

## Context

The project needs a name that strangers can find, a home on GitHub, and wording that makes clear it is not an
M5Stack product.

The name check on 2026-10-28 found:

- GitHub user/org `crossmono` free, and no repositories named `crossmono`.
- `crossmono.dev`, `.org`, `.app` and `.io` unregistered.
- `crossmono.com` and `@crossmono.bsky.social` belong to "＋Mono｜クロスモノ", a Japanese camera blog. That is a
  different field, so confusion is unlikely.
- X, Instagram and Reddit could not be checked automatically.

Other community projects already run on the PaperMono: crossplay-papermono, SeeSeeBook, KEY-HORSE (Meshtastic,
MeshCore, LoRaWAN), dayring-mono, PaperMono-Launcher, papermono-shopping-list, Nostos, m5-touch-card,
paper_name_plate and zephyr-mono.

## Options considered

1. **Keep the name CrossMono.** It says "CrossPoint on the PaperMono" in one word and it is free where it matters
   (GitHub, the main domains). The `.com` and Bluesky namesake is unrelated.
2. **Pick a new name.** No clear gain, and it loses the link to CrossPoint.

For the home:

1. **Personal account only.** Simplest, but the website needs a stable `*.github.io` address that does not depend
   on one person's account name.
2. **Organisation from the start for everything.** More setup before there is any code.
3. **Firmware under the personal account, website in an organisation** (chosen). The firmware can move into the
   organisation later; GitHub redirects transferred repositories.

## Decision

- The name stays **CrossMono**.
- The firmware lives at `nandanito/crossmono`. The GitHub organisation `crossmono` (created by Nandan on
  2026-10-29) holds `crossmono/crossmono.github.io`, the website with the web flasher and the docs, served at
  https://crossmono.github.io.
- The firmware repository may be transferred to the organisation later.
- Nandan checks the X and Instagram handles by hand. This is optional and does not block anything.
- Standard wording, used in the README, the website footer and announcements:

  > CrossMono is independent community firmware. It is not affiliated with or supported by M5Stack. PaperMono is
  > a product of M5Stack.

- Scope: CrossMono is reading-first firmware for the PaperMono and the PaperMono-Lite. The PaperMono hardware that
  CrossPoint does not use (LEDs, buzzer, IMU, RTC wake, NFC, LoRa, microphone) is the reason the project exists
  beside CrossPoint. It is added in our own files without making reading worse ([0008](0008-hardware-features.md)).
  Upstream's `SCOPE.md` stays unchanged and governs anything we propose upstream.

## Consequences

- Links to the firmware repository will change if it is transferred. GitHub redirects web links, git remotes and
  API calls. Released firmware has the OTA URL compiled in; `HttpDownloader` follows up to 5 redirects
  (`src/network/HttpDownloader.cpp:21`), but test an update across the redirect before transferring, and ship a
  release with the new URL soon after ([0009](0009-install.md)).
- The domains were not bought. If we want one, it should be registered before launch announcements.

## Sources

- Name check, 2026-10-28: GitHub search, domain lookups, crossmono.com, bsky.app/profile/crossmono.bsky.social
- GitHub docs, transferring a repository (redirects):
  https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository
