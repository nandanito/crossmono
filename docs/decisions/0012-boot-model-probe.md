# 0012. Boot model probe

- Status: Accepted; the Lite tester before `0.1.0` (Consequences) is replaced by [0013](0013-lite-untested-at-0-1-0.md)
- Date: 2026-11-04

Line references in this record are at `main` `ddd5218a` (CrossPoint base `42d58daa`, FreeInk SDK `5e94fe7`), not
at the bootstrap base.

## Context

[ADR 0003](0003-two-models.md) chose one build for both models and a boot probe with two parts: raise M5IOE1 IO4
(NFC_EN) and look for an ACK at 0x50; raise M5PM1 GPIO2 (LoRa_EN), pulse M5IOE1 IO10 (LoRa reset) and read the
SX1262 status. Facts found while planning and building 0.1.0:

- **Schematics V0.6.2.** On the Lite the NFC daughterboard connector, the SX1262 module and the LoRa load switch are
  not populated. IO4, IO10, IO2 and PM1 GPIO2 end at open nets ("PYB_NFC_EN is a spare GPIO pin"), so driving them
  is harmless there. On the full model the schematic routes IO4 to the NFC board's supply switch, but see the
  measurement below.
- **An SX1262 read is not a test on the Lite.** MISO (GPIO40) ends at the empty module footprint and floats, so a
  status read returns noise.
- **M5Stack's factory firmware** serves both models from one image and checks only the NFC chip
  (`m5stack/M5PaperMono-UserDemo` `ae6cd52`, `main/hal/hal_board.cpp:152-198`): IO4 high, 50 ms, then up to five
  reads of the ST25R3916 IC identity register (direct-read command 0x7F at I2C 0x50), 20 ms apart. The chip is
  there when the type bits [7:3] are 5 and the revision bits [2:0] are not 0. IO4 goes low again afterwards. It
  never probes LoRa.
- **The SDK leaves the radio pins alone.** `ensureBooted()` drives only the SDK's own expander pins low
  (`m5ioe1::OUTPUT_MASK`, `freeink-sdk/libs/hardware/BoardConfig/include/M5Ioe1.h:58`). Nothing in the SDK writes
  IO2, IO4, IO10 or PM1 GPIO2. The expander restarts with the PMIC on every wake and comes up with all pins as
  inputs; across a warm reset it keeps its registers. On our full model IO4 was an input (expander mode register
  0x39B4) and 0x50 answered an I2C scan.
- **Measured on our full model (2026-11-04, test build).** With IO4 held low as an output for a whole session
  (expander mode 0x3BBE, out 0x1020), the ST25R3916 still answered at 0x50 after a warm restart and returned its
  identity 0x2A, at once and again 300 ms later; the same after a PMIC wake with IO4 driven low in that boot. So on
  this unit IO4 low does not remove the chip's supply. Where its supply comes from is not known (the schematic shows
  a 0R link at the supply switch). Whether PM1 GPIO2 low switches the LoRa supply off cannot be checked from software.
- **PM1 GPIO2 registers**, confirmed in the M5PM1 datasheet (English, `m5stack/M5PM1` `docs/`) and in M5Stack's
  library (`m5stack/M5PM1` `315d2899`, `src/M5PM1.h:178-210`, `src/M5PM1.cpp:2214-2378`): MODE 0x10 bit 2
  (1 = output), OUT 0x11 bit 2, DRV 0x13 bit 2 (0 = push-pull; reset value 0x1F, open-drain), PU/PD_0 0x14
  bits [5:4] (00 = none), FUNC0 0x16 bits [5:4] (00 = GPIO). No SDK code uses PM1 GPIO2 (the frontlight uses GPIO3,
  the RTC interrupt GPIO0).
- **Every wake is a cold boot** through the PMIC, so "once per boot" is the only lifetime a result can have
  without storing it.
- **The probe needs the expander.** After a PMIC restart the expander can miss the SDK's first probe (GitHub #4);
  `mono::beginInput()` (`src/main.cpp:598`) waits for it before the input bring-up.

## Options considered

1. **ADR 0003 as written.** The LoRa part cannot work on the Lite (floating MISO), and an ACK at 0x50 alone accepts
   any chip at that address.
2. **NFC identity only, M5Stack's sequence** (chosen). Proven by the vendor on both models; one register read.
3. **Probe once and store the result in NVS.** Saves about 60 ms per boot, but a wrong result would stay until the
   store is cleared, and NVS is erased by a full flash anyway.

## Decision

- The probe reads the ST25R3916 identity, with M5Stack's sequence and timings. It runs once per boot in `setup()`,
  right after `halTiltSensor.begin()` (`src/main.cpp:630`): after `mono::beginInput()`, before the SD card and the
  settings. The result stays in RAM for that boot. Nothing is stored.
- If the expander cannot be written, no read is tried and the result is PaperMono-Lite, as in M5Stack's firmware.
  The log line then shows `NFC skipped` and is an error line.
- Every boot, on both models, holds the radio pins low: IOE1 IO2, IO4 and IO10 become push-pull outputs, low,
  pulls off; PM1 GPIO2 becomes a plain push-pull output, low, no pull. The PMIC writes run during the 50 ms NFC
  settle time. This gives the pins a known state and matches M5Stack's firmware for NFC_EN; it is not a power
  saving we can show (see the measurement above).
- One log line, `[MONO] Model probe: NFC <identity> -> <model> in <n> ms; radio pins low (...)`, with the read-back
  of the IOE1 OUT and MODE registers and the PM1 GPIO OUT and MODE registers. It is an error line when the read-back
  does not show the pins low.
- The **Model** setting (System): **Auto** (default) / **PaperMono** / **PaperMono-Lite**, saved with the other
  settings as `modelOverride`. It is read on every use, so a change applies at once; the probe still runs, so Auto
  shows the detected model again.
- About gets a **Model** row: "PaperMono (detected)", "PaperMono-Lite (manual)" and so on, in English like the rest
  of About.
- Home shows the model from 0.2.0, with the model badge (theme work, [ADR 0007](0007-ui.md)), not in 0.1.0. The
  header's right-hand label was tried and rejected on the device: FreeInkUI draws that label only next to a title
  (`freeink-sdk/libs/ui/FreeInkUI/include/components/controls/header.h:239-262`), and with an empty title on Home it
  sat on a row below the battery while Lyra drew its header rule on the cover tile's top edge
  (`src/components/themes/BaseTheme.cpp:465`).
- This record replaces the "Boot probe" bullet of ADR 0003 and moves its "shown on Home" to 0.2.0. The rest of 0003
  stands.

## Consequences

- Boot time: 79-80 ms measured on the full model (2026-11-04, every boot). About 155 ms is expected on the Lite (no
  chip answers, so all five reads run), estimated from the bus timings.
- Our code writes the radio pins (`src/mono/Model.cpp`) until the FreeInk SDK names them. The SDK proposal (roadmap
  0.1.0, "pin glue") adds the pins to the SDK's boot state and helpers to switch them; the sync that brings it
  switches `Model.cpp` to those helpers. The probe itself stays in our firmware: the SDK gets the mechanism, we keep
  the policy.
- NFC and LoRa features (0.4.0, 0.5.0) raise the pins only while in use and lower them again.
- A community tester with a Lite must confirm the Lite path before `0.1.0` stable (ADR 0003). (Replaced by
  [0013](0013-lite-untested-at-0-1-0.md): `0.1.0` is released with the Lite marked untested.)

## Sources

- Schematics V0.6.2 (2026-05-22): `PaperMono_SCH_V0.6.2_20260522.pdf`, `PaperMono-Lite_PRJ_V0.6.2_20260522.pdf`,
  linked from M5Stack's PaperMono product pages on docs.m5stack.com
- https://github.com/m5stack/M5PaperMono-UserDemo (MIT), `main/hal/hal_board.cpp:152-198` at `ae6cd52`
- https://github.com/m5stack/M5PM1 (MIT) at `315d2899`: `src/M5PM1.h`, `src/M5PM1.cpp`, `docs/M5PM1_Datasheet_EN.pdf`
- `freeink-sdk/libs/hardware/BoardConfig/include/M5Ioe1.h`, `PaperMonoBoard.h` (SDK `5e94fe7`)
- GitHub #4 (touch after wake) and `src/mono/InputBringUp.cpp`
