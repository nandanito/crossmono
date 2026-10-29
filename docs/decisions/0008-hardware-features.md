# 0008. Hardware features

- Status: Accepted
- Date: 2026-10-28

## Context

The PaperMono has hardware that CrossPoint does not use. Using it is what makes CrossMono more than a CrossPoint
build. Common to both models:

| Part | Wiring | State in CrossPoint at the base |
|---|---|---|
| LEDs | red on M5PM1 (on/off only), green M5IOE1 IO8, blue M5IOE1 IO9 | SDK `LedManager` exists, not linked |
| Buzzer | GPIO42 | SDK `Buzzer` exists, not linked |
| IMU | BMI270 at 0x68, INT1 to M5PM1 GPIO4 (not used) | Profile has `ImuType::Bmi270` (`freeink-sdk/libs/hardware/BoardConfig/include/BoardConfig.h:1183`); see below |
| RTC | RX8130CE at 0x32, INT to M5PM1 GPIO0 | Countdown wake via `freeink::papermono::setRtcWake` (`freeink-sdk/libs/hardware/BoardConfig/include/PaperMonoBoard.h:66`); no calendar alarm |
| Microphone | PDM, CLK 45, DATA 46; power on M5IOE1 IO12, which firmware must raise | SDK `Microphone` exists, not linked |

Full model only ([0003](0003-two-models.md)): ST25R3916 NFC, SX1262 LoRa.

Sleep is a PMIC shutdown (`requestShutdown()`); wake is a cold boot, or an RX8130 countdown through M5PM1 GPIO0.

**IMU at the base.** The pinned SDK `a5d5332` already contains BMI270 support for the PaperMono (FreeInk SDK PR
#152) and the power-down after a failed start (#159). CrossPoint's tilt page turn (`lib/hal/HalTiltSensor.cpp`) is
shown whenever the IMU probe succeeds (`src/SettingsList.cpp:184-187`). So tilt page turning may already work on
the PaperMono at our base; this must be checked on the device.

## Decision

Order of work: cues and sensors first (0.2.0), then NFC (0.4.0), then LoRa (0.5.0), then microphone and AI
(0.6.0). The CrossMono theme and navigation bar (0.3.0) sit between the first two ([docs/roadmap.md](../roadmap.md)).

### Cues and sensors (0.2.0)

- LED and buzzer cues (for example charging, low battery, timer done, errors).
- The model badge from [0003](0003-two-models.md).
- IMU: tilt page turn and rotation. Start by checking the existing tilt page turn on the device, since the SDK
  support is already pinned.
- RTC timer wake through the RX8130 countdown. Upstream PR #3820 (timer wake) is open; prefer the upstream version
  if it lands.

### NFC (0.4.0)

| Option | Licence | Coverage |
|---|---|---|
| M5Unit-NFC v0.1.2 | MIT | Full ST25R3916 stack, including card emulation; depends on M5UnitUnified ≥ 0.5.7 |
| esphome_st25r | MIT | Reader only |
| ST RFAL / stm32duino ST25R3916 | Proprietary (ST SLA0051) | Full, but not under an open licence we can ship |

Decision: vendor the M5Unit-NFC core (MIT) with a thin shim for `Wire` and the M5IOE1 enable line. Scope: NFC-A,
NDEF read/write and tag emulation only. M5Stack's NFC tutorial uses the same library.

### LoRa (0.5.0)

- Driver: RadioLib (MIT), version ≥ 7.2.1 as in M5Stack's tutorial (868.0 MHz, BW 125 kHz, SF12, CR 4/5, sync
  word 0x34, 22 dBm).
- Protocol options:

  | Option | Licence | Notes |
  |---|---|---|
  | Meshtastic firmware and protobufs | GPL-3.0, trademark | Cannot be mixed into MIT firmware; name is a trademark |
  | espp/meshtastic | MIT, clean-room | Interoperates, but no PKI direct messages, MQTT or telemetry |
  | MeshCore | MIT | Separate ecosystem |
  | Own minimal encrypted protocol | ours | Small, fits device-to-device use between CrossMono readers |

  Decision: our own minimal encrypted protocol. KEY-HORSE already covers Meshtastic, MeshCore and LoRaWAN on the
  PaperMono for people who want those networks.
- Region rules: a region setting, and **no transmission until a region is set**. The firmware enforces duty cycle
  and dwell time per region. Japan is receive-only until listen-before-talk is implemented.

  | Region | Rule | Reference |
  |---|---|---|
  | EU868 | 1 % duty cycle | ETSI EN 300 220 |
  | US915 | 400 ms dwell time / frequency hopping | FCC Part 15.247 |
  | AS923 / JP | Listen-before-talk + 400 ms dwell | ARIB STD-T108 |
  | KR920 | Listen-before-talk | |
  | IN865 | No duty-cycle limit | |

  The module covers 868–923 MHz, so EU433 is not possible.

### Microphone and AI (0.6.0)

- The Claude API has no audio input, so speech goes to a speech-to-text service first.
- Pipeline: PDM microphone → WAV in PSRAM → pluggable speech-to-text → Claude.

  | Speech-to-text | List price (from aggregators, not verified; check before 0.6.0) |
  |---|---|
  | OpenAI gpt-4o-mini-transcribe | ≈ $0.003 / min |
  | OpenAI gpt-4o-transcribe, whisper-1 | ≈ $0.006 / min |
  | Deepgram Nova-3 | ≈ $0.0043 / min |
  | Groq whisper-large-v3-turbo | ≈ $0.04 / hour |

  Default: OpenAI transcription; alternative: Groq.

  | Claude model | Input / output per million tokens |
  |---|---|
  | `claude-opus-5-5` (default) | $4 / $20 |
  | `claude-sonnet-5-5` | $2 / $10 |
  | `claude-haiku-5-5` | $0.10 / $0.50 (prompts up to 100K tokens) |

- API keys are stored in NVS through CrossPoint's `DeviceSecret` (`lib/DeviceSecret/`) and entered in the device
  web UI, never typed on the device.
- The red LED is on while the microphone records. Recording happens only in an explicit session started by the
  user; there is no always-on listening.
- ESP-SR is not a general speech-to-text engine (Espressif licence; wake word and up to 300 commands). It could
  provide a wake word later, nothing more.

### Where drivers live

- New drivers start in our repository in the FreeInk SDK style: `lib/mono-<name>/{include,src,test/host,library.json}`,
  consumed through `symlink://`, with stub bodies when the capability is off.
- When a driver is stable, we offer it to the FreeInk SDK. Pin glue (NFC_EN, LoRa_EN, antenna switch, radio reset)
  is proposed to the SDK early, following the `BoardT5S3::disableGpsLora()` precedent
  (`freeink-sdk/libs/hardware/BoardT5S3/include/BoardT5S3.h:24`). The SDK has merged our work quickly before (PR
  #159 in under two hours).
- **SDK pin for 0.1.0:** we do not move the submodule ourselves; we use the pin upstream ships. At the base that is
  `a5d5332`. (The plan was written against `44427f8`; upstream moved the pin in the base commit itself.)

## Consequences

- Each feature adds code in our own folders, and at most a small seam where it must hook into upstream (settings
  list, activity registration). Seams are listed in [docs/upstream-sync.md](../upstream-sync.md).
- LoRa needs a legal review of the region table before 0.5.0 ships. Transmission stays off by default.
- AI features send user audio and text to third parties. 0.6.0 needs a privacy note in the docs and on the device
  before the first session.
- The prices above will change. They are recorded to compare options, not as promises.

## Sources

- M5Stack PaperMono docs: https://docs.m5stack.com/en/arduino/papermono/lora, https://docs.m5stack.com/en/arduino/papermono/nfc,
  https://docs.m5stack.com/en/arduino/papermono/mic, https://docs.m5stack.com/en/arduino/papermono/wakeup,
  https://docs.m5stack.com/en/arduino/papermono/m5pm1_m5ioe1
- m5stack/M5PaperMono-UserDemo (MIT; pins RadioLib 7.2.1 and M5Unit-NFC 0.1.0), M5PaperMono-OTP-Demo,
  M5PaperMono-PowerDemo, M5_Hardware schematic V0.6.2
- RadioLib: https://github.com/jgromes/RadioLib; M5Unit-NFC: https://github.com/m5stack/M5Unit-NFC
- espp/meshtastic, MeshCore, Meshtastic firmware licences (checked 2026-10-28)
- ETSI EN 300 220, FCC 47 CFR 15.247, ARIB STD-T108
- Claude model IDs and prices: Claude API model table (cached 2026-10-06); no audio input (feature requests
  February and July 2026)
- `lib/hal/HalTiltSensor.cpp`, `src/SettingsList.cpp:184-187`, `lib/DeviceSecret/` at `60d3c8bb`;
  `freeink-sdk/libs/hardware/BoardConfig/include/{BoardConfig.h,PaperMonoBoard.h}` at `a5d5332`
