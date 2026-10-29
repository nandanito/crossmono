# CrossMono roadmap

Milestones are worked on in order. A milestone is done when every acceptance criterion is checked. The reasons
behind each item are in [docs/decisions/](decisions/README.md).

The root [`ROADMAP.md`](../ROADMAP.md) is CrossPoint's roadmap, inherited with the history. This file is
CrossMono's.

## 0.1.0: first release

CrossPoint with CrossMono's identity, installable by strangers, on both models.

Acceptance criteria:

- [ ] Boots on both models from a full flash with the new partition table ([0005](decisions/0005-partitions.md)).
- [ ] Model detected at boot and shown in About and on Home; manual override works
      ([0003](decisions/0003-two-models.md)).
- [ ] Branding: boot logo, name, About (with the CrossPoint base version and SDK commit), USB product strings,
      web UI header ([0007](decisions/0007-ui.md)).
- [ ] OTA reads our releases and uses our asset names ([0009](decisions/0009-install.md)).
- [ ] CI builds the development and release environments and runs the host tests, including the partition table
      test and the flash-size gate ([0010](decisions/0010-quality-and-ci.md)).
- [ ] The release workflow produces the OTA image, the full image, the `.elf`, `SHA256SUMS` and `manifest.json`.
- [ ] The flasher page on crossmono.github.io works in Chrome and Edge.
- [ ] Install docs, including the esptool fallback and the MBR-only SD card warning.
- [ ] README for strangers, `LICENSE` line, `THIRD-PARTY-NOTICES`, `CONTRIBUTING`, `SECURITY`, issue templates,
      `CHANGELOG.md` ([0011](decisions/0011-community-launch.md)).
- [ ] `0.1.0-rc.1` published as a GitHub pre-release.
- [ ] Hardware checklist passed on the full model; the Lite verified by a community tester before `0.1.0`
      ([hardware-test-checklist.md](hardware-test-checklist.md)).

Upstream-facing work:

- Merge CrossPoint `2.0.0` when it is tagged ([upstream-sync.md](upstream-sync.md)).
- Propose the NFC/LoRa enable and reset pins (pin glue for the model probe) to the FreeInk SDK.
- At the first release candidate: ask for a Lite tester; open a PR adding CrossMono to CrossPoint's
  "Community forks" list (text written by Nandan).

## 0.2.0: cues and sensors

Acceptance criteria:

- [ ] LED and buzzer cues, each with a setting to turn it off.
- [ ] Model badge.
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
