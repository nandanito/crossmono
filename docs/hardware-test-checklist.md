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
      CrossPoint with its web installer (https://crosspointreader.com/install, M5PaperMono, stable release) on a
      device fresh from a CrossMono full flash, note which firmware boots, and write the result into
      [install.md](install.md#going-back-to-crosspoint). Then install CrossMono again with a full flash. On the
      PaperMono that installer rewrites the bootloader, the partition table, NVS and otadata (checked on
      2026-11-07), so a device that has updated over Wi-Fi (CrossMono on the second app slot) needs no run of its
      own; test that case too if CrossPoint's installer changes.

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
- [ ] Side keys: short press turns pages / moves the selection; hold (about 650 ms) gives Back / Confirm.
- [ ] Both side keys held (about 650 ms) go Home from the reader, the file browser, settings and a Wi-Fi screen,
      like the bottom-edge swipe. The frontlight panel and the list-style reader menu close instead; the toolbar
      reader menu (the default with touch) goes Home. On Home they do nothing. Letting go of the keys one after
      the other, quickly or after a second, moves no selection and opens nothing on Home. With Short Power Button
      Click set to Bookmark, the chord goes Home and adds no bookmark. While USB drive mode waits for the computer,
      the chord leaves it; once the computer has the card, nothing happens.
- [ ] Tilt page turn: Settings → Controls → Tilt Page Turn = Normal. In the reader, a quick flick of the device turns
      a page forward or back, in portrait and in landscape. Inverted swaps the two directions; Off stops it. The
      setting is listed only when the motion sensor was found at boot.

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
- [ ] The web UI opens at `http://crossmono.local/` on a joined network and in hotspot mode; the screen shows that
      address and its QR code. The hotspot is listed as `CrossMono-Reader`, and the router lists the device as
      `CrossMono-Reader-…`.
- [ ] Calibre Connect: Calibre finds the device and sends a book.
- [ ] Settings → Reader → Manage Fonts lists the fonts and downloads one. The list and the font come from GitHub,
      like updates.
- [ ] OTA from the previous release to this one (final releases only; candidates are installed by hand). 0.1.0 and
      0.2.0-rc.1 cannot update over Wi-Fi ([ADR 0015](decisions/0015-sdk-pin-ahead-of-a-release.md)), so for 0.2.0
      start from 0.2.0-rc.2.
- [ ] After OTA, settings and reading progress are kept.

## Model-specific

- [ ] PaperMono (full): the boot log line `[MONO] Model probe: NFC 0x2? -> PaperMono in <n> ms; radio pins low (...)`
      shows identity type 5 (0x29 to 0x2F) and the radio pins low: IOE1 out bits 1, 3 and 9 (IO2, IO4, IO10) clear and
      the same bits set in mode; PM1 out bit 2 clear and mode bit 2 set.
- [ ] PaperMono-Lite: the boot probe finds no NFC (`NFC none -> PaperMono-Lite`), and nothing hangs or resets.
      Without a Lite, write "Lite: untested" in the record and in the release notes
      ([ADR 0013](decisions/0013-lite-untested-at-0-1-0.md)).

## Added by later milestones

Add a section here when a milestone adds a feature (NFC, LoRa, microphone).

### Cues (0.2.0)

LED cues are awake-only: the LED cannot light while the device sleeps.

- [ ] After a boot, the LED is off.
- [ ] Serial log while each cue lights once (blue, green, red with the low-battery test build): no
      `Cues: LED read-back ... wrote ...` line. That line means a leg does not read back as written, and the LED
      would be retried on every pass.
- [ ] Wi-Fi on (join a network, the hotspot, or Check for Updates): blue on. Leave the Wi-Fi screen: blue off.
- [ ] USB drive mode: green on, also once the computer has the card. Leave it: green off.
- [ ] At 10 % or below, on battery: a short red flash every 30 s, and one double beep per boot when Sound is not
      Off. The first flash comes about 30 s after the level is reached, because one reading alone does not start the
      cue. Plug in USB: the flashes stop within a second or two. To test on a charged battery, build locally with
      `build_src_flags = -DCROSSMONO_LOW_BATTERY_PERCENT=95` in a `platformio.local.ini` environment that extends
      `env:papermono`; the cue then starts at 95 % and stops at 98 %. After USB has been plugged in, the flashes come
      back only once the level is low again, which can take several minutes: the PaperMono's level comes from the
      battery voltage, which stays high for a while after charging.
- [ ] Settings → Controls → Sound = Alerts + Keys: a short click on each key press and each tap. Alerts: no click.
      Off: silence.
- [ ] Alerts + Keys: open a large book from the file browser, start a Wi-Fi scan, and save a setting. The click stays
      short; a long tone means the buzzer waits for the main loop.
- [ ] Low-battery test build: read a chapter with page turns for two minutes. A flash may come late during a page
      refresh, but no 30 s period passes without one.
- [ ] Settings → System → LED Cues = Off: nothing lights, whatever the state. On again: the current cue shows.
- [ ] Sleep while blue or green is on: the LED goes off with the sleep screen. Wake: the cues come back.
- [ ] Night check: frontlight on, LED Cues Off, read a chapter: nothing lights or blinks.
- [ ] Holding both keys to go Home with Sound = Alerts + Keys: at most a click or two, no beep sequence.
