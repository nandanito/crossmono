# Changelog

Notable changes to CrossMono. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/);
version numbers follow [VERSIONING.md](VERSIONING.md).

Every tag, release candidates included, needs its own section, `## [<tag>] - YYYY-MM-DD`, with an **Upstream**
block. The release workflow uses that section as the release notes and stops without it. Use full URLs in a
section: the release page does not resolve links relative to the repository.

## [Unreleased]

### Upstream

- CrossPoint base: 2.0.0 (`42d58daa`)
- FreeInk SDK: `6a208c0`, ahead of the base's `5e94fe7`. It is the commit CrossPoint `develop` pins. For the
  PaperMono it also brings the SDK's touch bring-up fix (CrossMono's own fix for #4 stays until the next sync), a
  Bluetooth connect fix, and no repeated request after connecting.
- Changes in CrossPoint 2.0.0: <https://github.com/crosspoint-reader/crosspoint-reader/releases/tag/2.0.0>

## [0.2.0-rc.2] - 2026-11-11

The second release candidate for 0.2.0. It is 0.2.0-rc.1 with a newer FreeInk SDK; the main fix is that updates over
Wi-Fi and font downloads work again (under Fixed). Install it over USB, from the install page's test build or with
esptool; updates over Wi-Fi do not offer release candidates, and 0.1.0 and 0.2.0-rc.1 cannot update over Wi-Fi at
all. A USB install erases the Bluetooth pairings and the keys of protected books; books, settings and Wi-Fi networks
on the SD card stay. Bluetooth page turners have not been tested with this version's FreeInk SDK yet.

**Tested on the full PaperMono only.** The PaperMono-Lite has not been tested yet, because we do not have one. It has
the same keys, LED and buzzer, so the new features should work on it. If you have a Lite, save a backup of the flash
before you install (<https://github.com/nandanito/crossmono/blob/main/docs/install.md#coming-from-m5stacks-firmware>),
and please tell us how it went in an issue (<https://github.com/nandanito/crossmono/issues/new/choose>).

### Added

- Holding both side keys goes Home from any screen
  ([#5](https://github.com/nandanito/crossmono/issues/5)).
- LED and sound cues: the LED is blue while Wi-Fi is on, green in USB drive mode, and flashes red every 30 s on
  battery at 10 % or below. With Sound at Alerts or Alerts + Keys, the device beeps twice the first time the battery
  gets low after each start; at Alerts + Keys it also clicks for each key press and tap. Settings → System → LED
  Cues (On by default) and Settings → Controls → Sound (Off, Alerts, Alerts + Keys; Off by default).

### Changed

- Holding both side keys no longer puts the device to sleep. The power button still does.
- The device's network names are CrossMono's: the web interface and Calibre Connect answer at
  `http://crossmono.local/` instead of `crosspoint.local`, the hotspot is `CrossMono-Reader`, and routers list
  `CrossMono-Reader-…` ([#16](https://github.com/nandanito/crossmono/issues/16)). Bookmarks to
  `crosspoint.local` need the new address.

### Fixed

- Updates over Wi-Fi ended with "Update Failed" since GitHub made a header in its download answers longer than the
  FreeInk SDK could read. Font downloads (Settings → Reader → Manage Fonts) use the same kind of GitHub link and get
  the same fix. The fix is in the FreeInk SDK, which is now at `6a208c0`
  (<https://github.com/nandanito/crossmono/blob/main/docs/decisions/0015-sdk-pin-ahead-of-a-release.md>). Devices on
  0.1.0 or 0.2.0-rc.1 cannot get this fix over Wi-Fi: install the new version from the install page
  (<https://crossmono.github.io>) or with esptool.

### Upstream

- CrossPoint base: 2.0.0 (`42d58daa`)
- FreeInk SDK: `6a208c0`, ahead of the base's `5e94fe7`. It is the commit CrossPoint `develop` pins. For the
  PaperMono it also brings the SDK's touch bring-up fix (CrossMono's own fix for #4 stays until the next sync), a
  Bluetooth connect fix, and no repeated request after connecting.
- Changes in CrossPoint 2.0.0: <https://github.com/crosspoint-reader/crosspoint-reader/releases/tag/2.0.0>

## [0.2.0-rc.1] - 2026-11-11

The first release candidate for 0.2.0: CrossMono works from the keys and tells you what it is doing. Install it by
hand from the install page's test build or with esptool; updates over Wi-Fi do not offer release candidates. A USB
install erases the Bluetooth pairings and the keys of protected books; books, settings and Wi-Fi networks on the SD
card stay.

**Tested on the full PaperMono only.** The PaperMono-Lite has not been tested yet, because we do not have one. It has
the same keys, LED and buzzer, so the new features should work on it. If you have a Lite, save a backup of the flash
before you install (<https://github.com/nandanito/crossmono/blob/main/docs/install.md#coming-from-m5stacks-firmware>),
and please tell us how it went in an issue (<https://github.com/nandanito/crossmono/issues/new/choose>).

### Added

- Holding both side keys goes Home from any screen
  ([#5](https://github.com/nandanito/crossmono/issues/5)).
- LED and sound cues: the LED is blue while Wi-Fi is on, green in USB drive mode, and flashes red every 30 s on
  battery at 10 % or below. With Sound at Alerts or Alerts + Keys, the device beeps twice the first time the battery
  gets low after each start; at Alerts + Keys it also clicks for each key press and tap. Settings → System → LED
  Cues (On by default) and Settings → Controls → Sound (Off, Alerts, Alerts + Keys; Off by default).

### Changed

- Holding both side keys no longer puts the device to sleep. The power button still does.
- The device's network names are CrossMono's: the web interface and Calibre Connect answer at
  `http://crossmono.local/` instead of `crosspoint.local`, the hotspot is `CrossMono-Reader`, and routers list
  `CrossMono-Reader-…` ([#16](https://github.com/nandanito/crossmono/issues/16)). Bookmarks to
  `crosspoint.local` need the new address.

### Upstream

- CrossPoint base: 2.0.0 (`42d58daa`)
- FreeInk SDK: `5e94fe7`
- Changes in CrossPoint 2.0.0: <https://github.com/crosspoint-reader/crosspoint-reader/releases/tag/2.0.0>

## [0.1.0] - 2026-11-07

The first release. It is 0.1.0-rc.1 plus one fix: the web interface footer (under Fixed).

**Tested on the full PaperMono only.** The PaperMono-Lite has not been tested yet, because we do not have one. If you
have a Lite, save a backup of the flash before you install
(<https://github.com/nandanito/crossmono/blob/main/docs/install.md#coming-from-m5stacks-firmware>), and please tell
us how it went in an issue (<https://github.com/nandanito/crossmono/issues/new/choose>).

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
- Updates come from CrossMono's GitHub releases. An image larger than the app slot is refused before the slot is
  erased.

### Fixed

- Touch sometimes did not come back after sleep and wake
  ([#4](https://github.com/nandanito/crossmono/issues/4)).
- The web interface footer said "Open source under the MIT license". It now says that the code is MIT-licensed and
  that the firmware image is GPLv3, because it includes wolfSSL.

### Upstream

- CrossPoint base: 2.0.0 (`42d58daa`)
- FreeInk SDK: `5e94fe7`
- Changes in CrossPoint 2.0.0: <https://github.com/crosspoint-reader/crosspoint-reader/releases/tag/2.0.0>

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
