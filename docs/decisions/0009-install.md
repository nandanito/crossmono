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
