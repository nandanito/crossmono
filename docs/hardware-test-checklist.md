# Hardware test checklist

Run this before every release candidate and every final release, with a build of the commit that will be tagged.
Copy the list into the release PR or issue and tick each item. Write down what failed and on which model.

- Version tested:
- Model: PaperMono (full) / PaperMono-Lite
- Tester:
- Date:

## Install

- [ ] Full flash of `crossmono-<version>-papermono-full.bin` at 0x0 from the web flasher (Chrome or Edge).
- [ ] Full flash with the esptool command from the install docs.
- [ ] First boot after a full flash shows the CrossMono boot screen and reaches Home.
- [ ] About shows the CrossMono version, the CrossPoint base and the SDK commit.
- [ ] Model detected correctly (About). Override setting switches it, and Auto restores detection.
- [ ] Going back to CrossPoint (final releases; once before `0.1.0`, then when the install path changes). Install
      CrossPoint with its web installer (https://crosspointreader.com/#flash-tools) twice: on a device fresh from a
      CrossMono full flash, and on one that has installed a CrossMono update over Wi-Fi (it then runs from the
      second app slot). Note which firmware boots each time, and write the result into
      [install.md](install.md#coming-from-m5stacks-firmware). Then install CrossMono again with a full flash.

## Storage

- [ ] SD card formatted MBR/FAT32 mounts; books open.
- [ ] SD card formatted GPT is refused with a clear message (not a crash).
- [ ] USB drive mode: the card appears on a computer; files copied there open on the device afterwards.

## Navigation (touch and keys)

Every screen must be possible to leave.

- [ ] Home, file browser, settings, reader: Back works (header button or left-edge swipe).
- [ ] Reader: bottom-edge swipe up goes Home.
- [ ] Reader: centre tap opens the reader menu; its Go Home entry works.
- [ ] Top-edge swipe or status-bar tap opens the frontlight Control Center.
- [ ] Full-screen messages and storage-exclusive screens (USB drive, firmware update) can be left.
- [ ] Side keys: short press turns pages / moves the selection; hold (about 650 ms) gives Back / Confirm; both keys
      together give Power.

## Power

- [ ] Power-button click with the default setting puts the device to sleep (shutdown).
- [ ] Power-button click with each alternative binding (Bookmark, Sync, Reader menu, Page turn, Force refresh)
      does that action, and auto-sleep still powers the device off.
- [ ] Wake from sleep returns to the same book and page.
- [ ] Touch works after every wake: five times, click the power button to sleep, wait about 15 s, click to wake,
      tap. Home must not show the four key hints at the bottom, which appear when the firmware found no touch
      controller (GitHub #4).
- [ ] Long hold of the power button still enters download mode (PMIC behaviour, needed for recovery).

## Display and light

- [ ] Page turns are clean; a half refresh happens at the configured interval; no lasting ghosting after sleep.
- [ ] Covers and the sleep screen show grey correctly.
- [ ] With the sleep screen set to Dark (the default) or Light, it shows the CrossMono logo and name.
- [ ] Frontlight on, off and brightness steps.

## Battery

- [ ] Battery percentage is plausible, and changes while charging over USB.

## Network and update

- [ ] Wi-Fi connects; the web UI opens and shows the CrossMono header, footer, tab title and icon.
- [ ] OTA from the previous release to this one (final releases only; candidates are installed by hand).
- [ ] After OTA, settings and reading progress are kept.

## Model-specific

- [ ] PaperMono (full): the boot log line `[MONO] Model probe: NFC 0x2? -> PaperMono in <n> ms; radio pins low (...)`
      shows identity type 5 (0x29 to 0x2F) and the radio pins low: IOE1 out bits 1, 3 and 9 (IO2, IO4, IO10) clear and
      the same bits set in mode; PM1 out bit 2 clear and mode bit 2 set.
- [ ] PaperMono-Lite: the boot probe finds no NFC (`NFC none -> PaperMono-Lite`), and nothing hangs or resets.
      Without a Lite, write "Lite: untested" in the record and in the release notes
      ([ADR 0013](decisions/0013-lite-untested-at-0-1-0.md)).

## Added by later milestones

Add a section here when a milestone adds a feature (cues and sensors, NFC, LoRa, microphone).
