# 0009. Install and update

- Status: Accepted
- Date: 2026-10-28

## Context

- The first install of CrossMono must write the partition table, so it is a full USB flash of a merged image at 0x0
  ([0005](0005-partitions.md)).
- CrossPoint releases one app image per board (`crosspoint-<version>-<board>.bin`, `.github/workflows/release.yml:116`)
  and has no merged image. Its web flasher (`crosspoint-tools`) supports the X3/X4 only.
- The local release build already produces `firmware.factory.bin` (5,426,288 B, starts with the 0xE9 image magic
  byte). CrossNext builds its full image with `esptool merge-bin` and checks the magic byte and version
  (`CrossNext-PaperMono/scripts_local/ship.sh`).
- ESP Web Tools needs a manifest `{name, version, builds: [{chipFamily: "ESP32-S3", parts: [{path, offset}]}]}`,
  an HTTPS page, and CORS on the firmware host. Serving the firmware from the same GitHub Pages site avoids CORS.
  Web Serial works in desktop Chrome and Edge; not in Safari, Firefox, iOS or Android.
- KEY-HORSE already runs a GitHub Pages flasher for the PaperMono, so the approach works on this device.
- The SD card is mounted as an MBR partition 1 only (`freeink-sdk/libs/hardware/SDCardManager/src/SDCardManager.cpp:58`,
  SdFat `FsVolume::begin` default partition 1). Cards formatted with GPT are not mounted.
- OTA reads `releases/latest` of a GitHub repository (`src/network/OtaUpdater.cpp:22`).

## Options considered

1. **esptool command line only.** Works everywhere, but strangers must install Python tools.
2. **ESP Web Tools page on crossmono.github.io, with esptool as the fallback** (chosen). One click in Chrome or
   Edge.
3. **Ask CrossPoint's `crosspoint-tools` to add the PaperMono.** Not in our control, and it would install
   CrossPoint's partition table.

## Decision

- Every release has these assets:
  - `crossmono-<version>-papermono.bin`: OTA app image
  - `crossmono-<version>-papermono-full.bin`: merged image for 0x0
  - `crossmono-<version>-papermono.elf`: for crash decoding
  - `SHA256SUMS`
  - `manifest.json`: ESP Web Tools manifest
- The flasher is an ESP Web Tools page on https://crossmono.github.io. Each release copies its full image to the
  site, so the image is served from the same origin.
- Fallback: an esptool command in the install docs, for example
  `esptool --chip esp32s3 write-flash 0x0 crossmono-<version>-papermono-full.bin`.
- The install docs warn that the SD card must use MBR (not GPT), and say how to reformat it.
- OTA updates come from our own GitHub releases.

## Consequences

- The release workflow must produce and check the merged image (magic byte, size, version string inside) before
  uploading. Whether `firmware.factory.bin` can be used as is, or `esptool merge-bin` is needed, is checked in
  0.1.0 (which parts it contains and at which offsets).
- The website repository gets one firmware copy per release. Keep old copies small in number, or prune them, to
  stay well within GitHub Pages limits.
- Users on phones and tablets cannot flash from the browser; the docs say so plainly.
- Changing the OTA source to our repository is a seam (`src/network/OtaUpdater.cpp:22,57`).

## Sources

- ESP Web Tools: https://esphome.github.io/esp-web-tools/
- Web Serial browser support: https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API
- esptool: https://docs.espressif.com/projects/esptool/en/latest/esp32s3/
- `.github/workflows/release.yml:116`, `src/network/OtaUpdater.cpp:22,57` at `60d3c8bb`
- `freeink-sdk/libs/hardware/SDCardManager/src/SDCardManager.cpp:58` at `a5d5332`
- CrossNext-PaperMono `scripts_local/ship.sh`, README SD card warning
- GitHub Pages limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits

## Addendum 2026-11-04: the full image and the manifest

The open point in the Consequences is settled: `firmware.factory.bin` from pioarduino 55.03.311 is used as the full
image as is (bootloader at 0x0, partition table at 0x8000, otadata from `boot_app0.bin` at 0xE000, the app at
0x10000, gaps 0xFF). `scripts/mono/package_release.py` checks it before every release, because PlatformIO only
prints a warning when it cannot write it ([RELEASING.md](../../RELEASING.md#what-the-workflow-produces)).

The manifest has one part, the full image at offset 0. A four-part manifest (bootloader, table, otadata, app) with
`new_install_prompt_erase: true` would keep NVS when the user leaves "Erase device" unticked; it was not chosen for
0.1.0. The full image always blanks NVS, like the esptool fallback, needs one file, and shows strangers no erase
question. Without that key ESP Web Tools erases the whole flash before a new install anyway (esp-web-tools 10.4.0,
`src/install-dialog.ts`). NVS holds the device secret (it unlocks protected-book keys stored on the SD card and
derives the plugin device IDs), the Bluetooth pairings and the trusted-time floor; settings and books are on the SD
card. The manifest can change in a later release without a firmware change.

## Addendum 2026-11-05: the install page

The flasher page is live at https://crossmono.github.io (site repository `crossmono/crossmono.github.io`, PR #1,
merge commit `18e23424`). Facts that add to the record:

- **Pages deploys through GitHub Actions** (`pages.yml`), not from a branch. GitHub does not start a branch build of
  Pages for a commit pushed by a workflow with `GITHUB_TOKEN` (GitHub Docs, "Configuring a publishing source for
  your GitHub Pages site"), and the publish workflow pushes that way. The deploy serves only `index.html`, the two
  manifests and `firmware/`.
- **Publishing a release to the site** is a separate workflow, `publish-firmware.yml`, started by hand with the tag.
  It checks that the release exists (a pre-release for `-rc.N`, a normal release otherwise), downloads the full
  image, `manifest.json` and `SHA256SUMS`, checks them against `SHA256SUMS`, copies them to `firmware/<tag>/`, and
  points `manifest.json` (final release) or `manifest-rc.json` (test build) at that folder. It commits to `main` as
  `github-actions[bot]` and deploys.
- **Keep-previous rule:** a publish keeps the folders that the two manifests point at now and pointed at before it,
  and deletes the rest. GitHub Pages and its CDN cache files for 10 minutes, so a cached manifest can still point at
  the previous folder. Publishing the same tag again deletes nothing. Old versions stay on the GitHub releases.
- **Device check (2026-11-05, Chrome on macOS):** the install of a dry-run 0.1.0 image worked. The browser lists the
  device as "USB JTAG/serial debug unit (cu.usbmodem2101)", and only while it is awake: a sleeping PaperMono does
  not show up on USB, so the page's first step is to wake it. Edge was not tested.

Sources: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site,
`crossmono/crossmono.github.io` at `18e23424` (`.github/workflows/pages.yml`, `publish-firmware.yml`,
`scripts/publish-firmware.sh`, `firmware/README.md`).

## Erratum 2026-11-05: Web Serial in Firefox

The Context says Web Serial does not work in Firefox. Desktop Firefox has it since Firefox 151 (released
2026-05-19). MDN says the site first asks the user to install a generated site permission add-on. The page says
"Chrome or Edge"; Firefox 151 or newer "may work" but is not tested with CrossMono. Safari, phones and tablets still
cannot install.

Sources: https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/151,
https://blog.mozilla.org/en/firefox/firefox-web-serial-adafruit/ (Mozilla, 2026-05-21)

## Addendum 2026-11-06: the licence file

Every release gets one more asset, `crossmono-<version>-LICENSE.txt` (Nandan, 2026-11-06). The firmware image as a
whole is GPLv3 because it includes wolfSSL ([0011](0011-community-launch.md), addendum 2026-11-05), and people who
download a release do not have the source tree that `THIRD-PARTY-NOTICES` points into.

- `scripts/mono/release_license.py` writes it after the release build: a header (tag, source commit, FreeInk SDK
  commit, source links, the GPLv3 statement), `LICENSE`, `THIRD-PARTY-NOTICES`, the GPL-3.0 text, and the full text
  of every licence that `THIRD-PARTY-NOTICES` names. The library texts come from `.pio/libdeps/<env>` of that build,
  with the registry package or git commit each library came from. It also has the copyright notices in the
  Arduino-ESP32 sources that the build compiles (as CrossPoint's script collects them), and the notices of the
  third-party code in the prebuilt ESP-IDF archives that the link map shows in the image: TinyUSB, cJSON, Cadence's
  Xtensa runtime and HAL, TLSF and GCC's fast_float, and the copyright comments in the package headers of lwIP,
  FreeRTOS, wpa_supplicant, SD/MMC and Mbed TLS. The texts that no package has are quoted in
  `THIRD-PARTY-NOTICES` section 4. It stops when a text is missing, when a downloaded library is not in its list,
  or when a platform package is not the version whose link map was checked.
- `package_release.py` copies it into the assets, lists it in `SHA256SUMS`, and refuses a file that does not name
  the tag and both commits, has no GPLv3 statement, or lacks one of the expected texts.
- **Known limit** (Nandan, 2026-11-06): for the prebuilt ESP-IDF components the per-file notices come from the
  package headers, plus the holders quoted in `THIRD-PARTY-NOTICES`. A holder named only in a source file of a
  prebuilt component is not collected; a full audit of every linked source was left out of 0.1.0. Three Codex
  rounds checked the link map of the 0.1.0 image against this list.
- The texts that are not in the source tree or in the release job (GPL-3.0, LGPL-3.0, LPPL-1.3c, the hyphenation
  notices, the ESP-IDF component notices, the copied-code notices) come from `licenses/*.txt`: CrossPoint's files
  from its `develop` branch (`136c2655`), copied unchanged ahead of the sync that brings them, so that sync merges
  them without a conflict. The Lucide text comes from the nested SDK submodule, which the release job already
  checks out (`submodules: recursive`).
- The name has the version and `.txt`, like the other assets, so it opens on every system and stays unique next to
  other downloads. CrossPoint attaches a file named `LICENSE`; its script takes the output path as an argument, so
  our name can stay when its script replaces ours ([upstream-sync.md](../upstream-sync.md)).
- The install page will link to the file from its footer (a site PR). The site's `publish-firmware` downloads only
  the full image, `manifest.json` and `SHA256SUMS`, and checks only its two lines in `SHA256SUMS`, so the new
  entry does not change it.

Sources: `scripts/mono/release_license.py`, `scripts/mono/package_release.py`, `git show 136c2655 --stat`,
`crossmono/crossmono.github.io` `scripts/publish-firmware.sh:28-40` at `86596763`, release dry run 41848482046
(checkout log: `freeink-sdk/libs/assets/Icons/lucide` checked out at `c81680e0`).

## Addendum 2026-11-06: the first release candidate

`0.1.0-rc.1` was published on 2026-11-06 (pre-release, tag on `62f8bb6f`) and copied to the install page by
`publish-firmware`. In the device test, the install from the page worked in Brave, a Chromium-based browser, and the
esptool command from the install docs worked too. The page and `docs/install.md` now name Chrome, Edge and Brave;
other Chromium-based browsers and Firefox 151 or newer may work but are not tested. The page links each release's
licence file from its card and footer (site PR #3).

## Addendum 2026-11-07: the first release

`0.1.0` was published on 2026-11-07 (tag on `610bc2f1`), and `publish-firmware` made it the install page's only
build: publishing a final release empties `manifest-rc.json`. Facts from its device test on the full model:

- The install page works in Edge 157 too, so Chrome, Edge and Brave are tested.
- CrossPoint's installer (https://crosspointreader.com/install) on the PaperMono writes CrossPoint's bootloader, its
  own partition table, otadata and firmware, and erases NVS. So going back from CrossMono needs no extra step, and it
  does not matter whether CrossMono was installed over USB or updated over Wi-Fi. `docs/install.md` ("Going back to
  CrossPoint") describes it.
- The update from `0.1.0-rc.1` to `0.1.0` over Wi-Fi went into app1 (`Boots ota_1`, image state VALID) and kept
  settings and reading progress.
