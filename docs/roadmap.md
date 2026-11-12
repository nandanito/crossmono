# CrossMono roadmap

Milestones are worked on in order. A milestone is done when every acceptance criterion is checked. The reasons
behind each item are in [docs/decisions/](decisions/README.md).

The root [`ROADMAP.md`](../ROADMAP.md) is CrossPoint's roadmap, inherited with the history. This file is
CrossMono's.

## 0.1.0: first release

CrossPoint with CrossMono's identity, installable by strangers, on both models (the Lite untested at release,
[0013](decisions/0013-lite-untested-at-0-1-0.md)).

Acceptance criteria:

- [x] Boots on the full model from a full flash with the new partition table ([0005](decisions/0005-partitions.md)).
      The Lite is not tested ([0013](decisions/0013-lite-untested-at-0-1-0.md)).
- [x] Model detected at boot and shown in About; manual override works ([0003](decisions/0003-two-models.md),
      [0012](decisions/0012-boot-model-probe.md)).
- [x] Branding: boot logo, name, About (with the CrossPoint base version and SDK commit), USB product strings,
      web UI header ([0007](decisions/0007-ui.md)).
- [x] OTA reads our releases and uses our asset names ([0009](decisions/0009-install.md)).
- [x] CI builds the development and release environments and runs the host tests, including the partition table
      test and the flash-size gate ([0010](decisions/0010-quality-and-ci.md)).
- [x] CI runs the stack-budget check ([0010](decisions/0010-quality-and-ci.md)).
- [x] The release workflow produces the OTA image, the full image, the `.elf`, `SHA256SUMS` and `manifest.json`.
- [x] Each release also has a licence file with every licence text and the source commits
      ([0009](decisions/0009-install.md), [0011](decisions/0011-community-launch.md)).
- [x] The flasher page on crossmono.github.io works in Chrome and Edge. Chrome passed on 2026-11-05 with a dry-run
      image, Brave on 2026-11-06 with the `0.1.0-rc.1` build, and Edge 157 on 2026-11-07 with the `0.1.0-rc.1` build
      from the live page.
- [x] Install docs, including the esptool fallback and the MBR-only SD card warning
      ([install.md](install.md)).
- [x] README for strangers, `LICENSE` line, `THIRD-PARTY-NOTICES`, `CONTRIBUTING`, `SECURITY`, issue templates,
      `CHANGELOG.md` ([0011](decisions/0011-community-launch.md)).
- [x] `0.1.0-rc.1` published as a GitHub pre-release (2026-11-06).
- [x] Hardware checklist passed on the full model ([hardware-test-checklist.md](hardware-test-checklist.md)). For
      `0.1.0-rc.1` a shorter run passed on the full model (2026-11-06): both install paths, first boot, About, five
      sleep/wake cycles with touch, a book, USB drive mode and the web interface. The code had not changed since the
      earlier device tests. For `0.1.0` the full checklist passed on 2026-11-07 (record in
      [#19](https://github.com/nandanito/crossmono/pull/19)), including going back to CrossPoint, and after publishing
      the update from `0.1.0-rc.1` over Wi-Fi.
- [x] `0.1.0` published (2026-11-07, tag on `610bc2f1`).
- [x] The Lite is marked as untested in the release notes, the README, the install docs and on the install page,
      with a request for reports. We have no Lite, so a tester's report is welcome after the release
      ([0013](decisions/0013-lite-untested-at-0-1-0.md)).

Upstream-facing work:

- Merge CrossPoint `2.0.0` ([upstream-sync.md](upstream-sync.md)): synced to `42d58daa`, FreeInk SDK `5e94fe7`.
- Propose the NFC/LoRa enable and reset pins (pin glue for the model probe) to the FreeInk SDK. On hold: driving
  the pins low saves no power we can show ([0012](decisions/0012-boot-model-probe.md)), so the proposal goes with
  the first radio feature (0.4.0).
- Offer the OTA size check (an image larger than the slot is refused before the slot is erased) to CrossPoint. On
  hold: offered when CrossPoint's image nears its slot or the seam conflicts at a sync.
- With the `0.2.0` announcement (`0.1.0` was not announced, [0013](decisions/0013-lite-untested-at-0-1-0.md),
  addendum 2026-11-07): ask for a Lite tester; open a PR adding CrossMono to CrossPoint's "Community forks" list
  (text written by Nandan).

## 0.2.0: cues and keys

CrossMono works from the keys and tells you what it is doing. The FreeInk SDK already has the LED, buzzer and RTC
drivers, so 0.2.0 is firmware policy, not drivers ([0014](decisions/0014-cues-and-keys.md)).

Acceptance criteria:

- [x] Holding both side keys goes Home from any screen
      ([#5](https://github.com/nandanito/crossmono/issues/5)); the power button keeps its binding.
- [x] LED and sound cues (low battery, radio on, USB drive mode, optional key click), each with a setting to turn
      it off ([0014](decisions/0014-cues-and-keys.md)).
- [x] The device answers at `crossmono.local`, and its hotspot is `CrossMono-Reader`
      ([#16](https://github.com/nandanito/crossmono/issues/16)).
- [x] CrossPoint's tilt page turn checked on the device (0.2.0-rc.1 and 0.2.0-rc.2 checklists, 2026-11-11 and
      2026-11-12).
- [x] Hardware checklist extended for the new features and passed on the full model; the Lite per
      [0013](decisions/0013-lite-untested-at-0-1-0.md). For `0.2.0-rc.1` (2026-11-11) everything passed except
      updates over Wi-Fi, which failed on the old FreeInk SDK; that led to
      [0015](decisions/0015-sdk-pin-ahead-of-a-release.md) and `0.2.0-rc.2`. For `0.2.0-rc.2` (2026-11-12) the items
      the SDK change touches passed again in full, the rest in a quick pass. After publishing, the update from
      `0.2.0-rc.2` to `0.2.0` over Wi-Fi passed. Not tested: a Bluetooth page turner (no device) and the Lite.
- [x] `0.2.0-rc.1` (2026-11-11) and `0.2.0-rc.2` (2026-11-12) published as GitHub pre-releases.
- [x] `0.2.0` published (2026-11-12, tag on `fb6931ea`).

Moved out of 0.2.0 ([0014](decisions/0014-cues-and-keys.md)): the model badge on Home (to 0.3.0), IMU rotation
(left to CrossPoint) and the RTC timer wake (with the first feature that needs it; CrossPoint PR #3820 is an ESP
deep-sleep timer and does not apply to the PaperMono).

Upstream-facing work: after the device test, a CrossPoint PR text and patch for Home from the keys (Nandan posts;
drafted 2026-11-11); once the cues have run on the device, a CrossPoint Discussion about cues on boards with an LED
or a buzzer (text drafted for Nandan). If CrossPoint tags a release before the 0.2.0 tag, merge it first
([upstream-sync.md](upstream-sync.md)); none did, so 0.2.0 is on CrossPoint 2.0.0 with the FreeInk SDK that
CrossPoint `develop` pins ([0015](decisions/0015-sdk-pin-ahead-of-a-release.md)).

## 0.3.0: CrossMono interface

Acceptance criteria:

- [ ] CrossMono theme, in our files: 1-bit, anti-aliased text, grey only on covers, sleep screen and About.
- [ ] Visible touch navigation bar (FreeInk UI `gesture-bar`) on every screen, including the reader.
- [ ] Every screen can be left by a visible control, not only by a gesture.
- [ ] Model badge, which also shows the model on Home ([0012](decisions/0012-boot-model-probe.md),
      [0014](decisions/0014-cues-and-keys.md)).
- [ ] Opt-in "release candidate" update channel.

Upstream-facing work: report navigation gaps that also affect CrossPoint (screens that can be left only by
gesture).

## 0.4.0: NFC (full model)

Acceptance criteria:

- [ ] Vendored M5Unit-NFC core with a `Wire`/M5IOE1 shim; NFC-A, NDEF read/write, tag emulation.
- [ ] NFC is hidden on the Lite and powered down when not in use.
- [ ] `THIRD-PARTY-NOTICES` updated.

Upstream-facing work: offer the ST25R3916 driver to the FreeInk SDK once stable.

## 0.5.0: LoRa (full model)

Acceptance criteria:

- [ ] RadioLib driver for the SX1262; radio powered down when not in use.
- [ ] Region setting; no transmission until a region is set.
- [ ] Duty cycle and dwell time enforced per region; Japan receive-only until listen-before-talk exists.
- [ ] Own minimal encrypted protocol between CrossMono devices, documented.
- [ ] Region rules reviewed against current regulations before release.

Upstream-facing work: offer the SX1262 glue to the FreeInk SDK.

## 0.6.0: microphone and AI

Acceptance criteria:

- [ ] PDM recording into PSRAM as WAV; red LED on while recording; explicit sessions only.
- [ ] Pluggable speech-to-text (OpenAI by default, Groq as an alternative); Claude `claude-opus-5-5` by default.
- [ ] API keys entered in the device web UI and stored with `DeviceSecret`.
- [ ] Privacy note in the docs and on the device before the first session.
- [ ] Prices and model IDs re-checked against the providers.

## 1.0.0: stable

Criteria:

- [ ] Both models verified on every release.
- [ ] Upstream sync at most one CrossPoint release behind.
- [ ] No open P1 hardware bugs.
- [ ] Show HN post.
