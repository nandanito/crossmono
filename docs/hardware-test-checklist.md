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
- [ ] Model detected correctly (About / Home). Override setting switches it, and Auto restores detection.

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
- [ ] Long hold of the power button still enters download mode (PMIC behaviour, needed for recovery).

## Display and light

- [ ] Page turns are clean; a half refresh happens at the configured interval; no lasting ghosting after sleep.
- [ ] Covers and the sleep screen show grey correctly.
- [ ] Frontlight on, off and brightness steps.

## Battery

- [ ] Battery percentage is plausible, and changes while charging over USB.

## Network and update

- [ ] Wi-Fi connects; the web UI opens and shows the CrossMono header.
- [ ] OTA from the previous release to this one (final releases only; candidates are installed by hand).
- [ ] After OTA, settings and reading progress are kept.

## Model-specific

- [ ] PaperMono (full): NFC and LoRa are off after boot (when no feature uses them).
- [ ] PaperMono-Lite: boot probe finds no NFC/LoRa, and nothing hangs or resets.

## Added by later milestones

Add a section here when a milestone adds a feature (cues and sensors, NFC, LoRa, microphone).
