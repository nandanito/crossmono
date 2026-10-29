# 0003. PaperMono and PaperMono-Lite: one build

- Status: Accepted
- Date: 2026-10-28

## Context

M5Stack sells two models: **PaperMono** (C153) and **PaperMono-Lite** (C153-Lite). They share the ESP32-S3R8,
16 MB flash, 8 MB octal PSRAM, the SSD1677 480x800 panel, touch, frontlight, battery, microphone, buzzer, IMU, RTC,
microSD and the two keys. Only the full model has:

- **NFC:** ST25R3916 on I2C address 0x50, IRQ on GPIO6, enabled by M5IOE1 IO4 (NFC_EN).
- **LoRa:** SX1262 on SCK 39, MISO 40, MOSI 38, NSS 41, BUSY 21, IRQ 5; reset on M5IOE1 IO10, antenna switch on
  M5IOE1 IO2, power on M5PM1 GPIO2 (LoRa_EN); 868–923 MHz FPC antenna.

M5Stack links the same CrossPoint image for both models. The FreeInk SDK has no NFC, LoRa or Lite code. Its only
hint is a comment listing "0x50 (NFC on Pro)" (`freeink-sdk/libs/hardware/InputManager/src/InputManager.cpp:1635`).
The pins above are not used anywhere in the SDK.

Upstream issue #3446 ("Lite didn't boot on 1.6.0") turned out to be a bad release build (PSRAM settings,
#3331/#3428), not a hardware difference. It shows that a problem on one model can stay hidden when only the other
model is tested.

Only the full model is on hand for development.

## Options considered

1. **Two builds, two release files.** Clear at compile time. But CI and release work double, users must pick the
   right file, and the OTA asset name and board tag would need a second board name.
2. **One build, detect the model at boot** (chosen). One file for everyone. Costs a short probe at boot, and a
   wrong result must be correctable.
3. **One build, no detection.** Treat every device as a Lite until a feature needs the radios. Simple now, but the
   NFC and LoRa features would need detection later anyway.

## Decision

- One build, one release file for both models, model detected at runtime.
- Boot probe:
  - NFC: raise M5IOE1 IO4 (NFC_EN), then check for an I2C ACK at 0x50.
  - LoRa: raise M5PM1 GPIO2 (LoRa_EN), pulse M5IOE1 IO10 (reset), then read the SX1262 status.
- The result is cached and shown in About and on Home.
- A manual override setting: **Auto** (default) / **PaperMono** / **PaperMono-Lite**.
- The board tag stays `papermono`. Release assets: `crossmono-<version>-papermono.bin` (OTA image) and
  `crossmono-<version>-papermono-full.bin` (merged image for a first install).
- A community tester with a Lite must confirm the Lite path before `0.1.0` stable.

## Consequences

- The probe must be safe on a Lite. Before shipping it, check in the schematic (M5_Hardware V0.6.2) what IOE1 IO4,
  IOE1 IO10 and PM1 GPIO2 drive on the Lite, and lower the enables again after the probe when no chip answers.
- On the full model, NFC and LoRa stay powered down after the probe until a feature uses them.
- Where the cached result is stored and when it is probed again is decided in the 0.1.0 implementation.
- Every release checklist covers both models ([docs/hardware-test-checklist.md](../hardware-test-checklist.md)).

## Sources

- M5Stack PaperMono docs: https://docs.m5stack.com/en/arduino/papermono/lora, https://docs.m5stack.com/en/arduino/papermono/nfc,
  https://docs.m5stack.com/en/arduino/papermono/m5pm1_m5ioe1
- m5stack/M5PaperMono-UserDemo (MIT); M5_Hardware schematic V0.6.2
- `freeink-sdk/libs/hardware/BoardConfig/include/BoardConfig.h:1151-1190` (PaperMono profile, no NFC/LoRa fields)
- `src/network/FirmwareBoardTag.cpp:19,50` (board name `papermono`, tag `CROSSPOINT-BOARD-V1:papermono;`)
- https://github.com/crosspoint-reader/crosspoint-reader/issues/3446
