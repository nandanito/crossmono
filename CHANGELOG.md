# Changelog

Notable changes to CrossMono. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/);
version numbers follow [VERSIONING.md](VERSIONING.md).

Every tag, release candidates included, needs its own section, `## [<tag>] - YYYY-MM-DD`, with an **Upstream**
block. The release workflow uses that section as the release notes and stops without it. Use full URLs in a
section: the release page does not resolve links relative to the repository.

## [Unreleased]

### Upstream

- CrossPoint base: 2.0.0 (`42d58daa`)
- FreeInk SDK: `5e94fe7`

## [0.1.0-rc.1] - 2026-11-06

### Added

- PaperMono and PaperMono-Lite from one firmware image. The model is detected at boot and shown in About; Settings →
  System → Model overrides it (ADR 0012).
- About also shows the CrossPoint base version and the FreeInk SDK commit.
- Release assets: the OTA image, a full image for offset 0x0, the `.elf`, `SHA256SUMS` and a manifest for the web
  flasher (ADR 0009). Each release also has `crossmono-<version>-LICENSE.txt`, one text file with every licence
  in the firmware image and the exact source commits.
- An install guide (<https://github.com/nandanito/crossmono/blob/main/docs/install.md>) and the install page
  <https://crossmono.github.io>.
- Third-party notices: the licences of everything in the firmware image, and how to get the source of a release
  (<https://github.com/nandanito/crossmono/blob/main/THIRD-PARTY-NOTICES>). The firmware image as a whole is
  distributed under the GNU GPL version 3, because it includes wolfSSL; CrossPoint's and CrossMono's code is MIT.
- A stack-budget check in CI: each measured task's deepest call path against its stack (ADR 0010).

### Changed

- New partition table with two 7.9 MiB app slots and no SPIFFS (ADR 0005). The first install is a full flash; it
  erases the device secret and Bluetooth pairings, but not the SD card.
- CrossMono name and logo on the boot and sleep screens, in About, in the web interface and in the USB device
  names.
- CrossMono's own version numbers, starting at 0.1.0 (ADR 0004). The firmware's HTTP requests send
  `User-Agent: CrossMono-ESP32-<version>`.
- Updates come from CrossMono's GitHub releases. Without a release the device shows "No update available"; an
  image larger than the app slot is refused before the slot is erased.

### Fixed

- Touch sometimes did not come back after sleep and wake
  ([#4](https://github.com/nandanito/crossmono/issues/4)).

### Upstream

- CrossPoint base: 2.0.0 (`42d58daa`)
- FreeInk SDK: `5e94fe7`
- Changes in CrossPoint 2.0.0: <https://github.com/crosspoint-reader/crosspoint-reader/releases/tag/2.0.0>
