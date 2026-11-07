# CrossMono roadmap

Milestones are worked on in order. A milestone is done when every acceptance criterion is checked. The reasons
behind each item are in [docs/decisions/](decisions/README.md).

The root [`ROADMAP.md`](../ROADMAP.md) is CrossPoint's roadmap, inherited with the history. This file is
CrossMono's.

## 0.1.0: first release

CrossPoint with CrossMono's identity, installable by strangers, on both models (the Lite untested at release,
[0013](decisions/0013-lite-untested-at-0-1-0.md)).

Acceptance criteria:

- [ ] Boots on the full model from a full flash with the new partition table ([0005](decisions/0005-partitions.md)).
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
- [ ] Hardware checklist passed on the full model ([hardware-test-checklist.md](hardware-test-checklist.md)). For
      `0.1.0-rc.1` a shorter run passed on the full model (2026-11-06): both install paths, first boot, About, five
      sleep/wake cycles with touch, a book, USB drive mode and the web interface. The code had not changed since the
      earlier device tests.
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
- With the `0.1.0` announcement: ask for a Lite tester ([0013](decisions/0013-lite-untested-at-0-1-0.md)); open a
  PR adding CrossMono to CrossPoint's "Community forks" list (text written by Nandan).

## 0.2.0: cues and sensors

Acceptance criteria:

- [ ] LED and buzzer cues, each with a setting to turn it off.
- [ ] Model badge, which also shows the model on Home ([0012](decisions/0012-boot-model-probe.md)).
- [ ] IMU: tilt page turn checked on the device (the pinned SDK already supports the BMI270), and rotation.
- [ ] RTC timer wake through the RX8130 countdown.
- [ ] Hardware checklist extended for the new features and passed on both models.

Upstream-facing work: offer stable driver glue (LED, buzzer, RTC wake) to the FreeInk SDK; follow CrossPoint PR
#3820 (timer wake) and use it if it lands.

## 0.3.0: CrossMono interface

Acceptance criteria:

- [ ] CrossMono theme, in our files: 1-bit, anti-aliased text, grey only on covers, sleep screen and About.
- [ ] Visible touch navigation bar (FreeInk UI `gesture-bar`) on every screen, including the reader.
- [ ] Every screen can be left by a visible control, not only by a gesture.
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
