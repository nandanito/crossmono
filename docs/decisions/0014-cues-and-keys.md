# 0014. 0.2.0 uses the SDK's drivers; cues are firmware policy

- Status: Accepted
- Date: 2026-11-07

Line references in this record are at `main` `3da343fd`: CrossPoint base `42d58daa` (2.0.0), FreeInk SDK
`5e94fe7`.

## Context

[ADR 0008](0008-hardware-features.md) planned 0.2.0 as "cues and sensors": LED and buzzer cues, the model badge,
IMU tilt page turn and rotation, and an RTC timer wake. It also said new drivers start in `lib/mono-*` and are
offered to the FreeInk SDK when stable. Three things are now known that 0008 did not know.

**The pinned SDK already has the drivers.** CrossPoint links none of them for cues.

| Part | SDK at `5e94fe7` | Capability flag (on for the PaperMono) |
|---|---|---|
| RGB LED: red on the M5PM1, green and blue on M5IOE1 IO8 and IO9, on/off only | `LedManager`, with a PaperMono path and a non-blocking `flash()` / `update()` (`freeink-sdk/libs/hardware/LedManager/src/LedManager.cpp:49-105`, `239-250`) | `FREEINK_CAP_LED` (`freeink-sdk/libs/hardware/BoardConfig/include/BoardConfig.h:382`) |
| Passive buzzer on GPIO42 | `Buzzer` (LEDC). `tone(freq, ms)` blocks with `delay()`; `tone(freq, 0)` followed by `noTone()` does not (`freeink-sdk/libs/hardware/Buzzer/src/Buzzer.cpp:26-33`) | `FREEINK_CAP_BUZZER` (`BoardConfig.h:378`) |
| RX8130 countdown wake | `Rtc::armWakeTimer`, `cancelWakeTimer`, `readWakeTimer` (`freeink-sdk/libs/hardware/Rtc/include/Rtc.h:43-47`); `papermono::setRtcWake()` and `papermono::bootWakeState()` (`freeink-sdk/libs/hardware/BoardConfig/include/PaperMonoBoard.h:37`, `66`) | `FREEINK_CAP_RTC` (`BoardConfig.h:355`) |
| BMI270 IMU | `Imu`; CrossPoint's tilt page turn worked on the full model in the PR #10 device test | `FREEINK_CAP_IMU` (`BoardConfig.h:364`) |

**CrossPoint PR #3820 (timer wake) cannot apply to the PaperMono.** It adds an ESP deep-sleep timer (an `esp_sleep`
wake source). The PaperMono sleeps by a PMIC shutdown, with the ESP unpowered (`lib/hal/HalPowerManager.cpp:143-150`).
Its only timer wake is the RX8130 countdown through M5PM1 GPIO0, which the SDK already implements. On 2026-11-07
#3820 was still open, last changed on 2026-10-20.

**No LED can show while the device sleeps.** The M5PM1 clears `PWR_CFG`, which holds the red LED enable, on
shutdown (`freeink-sdk/libs/hardware/BoardConfig/include/M5Pm1.h:48-49`), and the ESP, which drives green and blue
through the IO expander, is off. A "charging" light while asleep is not possible. On the PaperMono, "on USB" and
"charging" are one signal: `HalGPIO::isUsbConnected()` reads the M5PM1 supply source (`lib/hal/HalGPIO.cpp:240-256`),
and the SDK sets `charging` to the same value (`freeink-sdk/libs/hardware/BatteryMonitor/src/BatteryMonitor.cpp:986-997`).

**There is no button path to Home** (GitHub #5). The two side keys give Up, Down, Back and Confirm, and holding both
keys is a second way to sleep, next to the power button. When touch fails (GitHub #4 on CrossPoint 2.0.0), some
screens cannot be left. The SDK reports the two-key chord as a *held* `BTN_POWER` whose held time counts from the
moment both keys went down (`freeink-sdk/libs/hardware/InputManager/src/InputManager.cpp:598-605`,
`TWO_BUTTON_HOLD_MS = 650`), and the power button as a one-tick `BTN_POWER` pulse (`InputManager.cpp:563-571`). The
firmware can tell them apart by the held time, with no SDK change.

0.1.0 was not announced. The first announcement comes with 0.2.0, so 0.2.0 has to give a PaperMono owner who runs
CrossPoint a reason to switch.

## Options considered

1. **Keep 0008's 0.2.0 as written.** Write `lib/mono-*` drivers for LED, buzzer and RTC, offer them to the SDK, and
   ship cues, the model badge, rotation and the timer wake. The drivers would duplicate the SDK's, and the badge,
   rotation and the timer wake each cost a seam or a device-test cycle without giving a user a reason to switch.
2. **Use the SDK's drivers and keep 0.2.0 to what a user notices.** Home from the keys, LED and sound cues, and the
   device's own network name. The cue policy is ours; the drivers are the SDK's.
3. **Cues only.** Smallest, but cues alone would not move a CrossPoint user.

## Decision

Option 2.

- **No `lib/mono-*` driver for the LED, the buzzer or the RTC.** 0.2.0 links the SDK's `LedManager` and `Buzzer` in
  the PaperMono environments only.
- **Cue policy lives in `src/mono/`**, with a pure policy function that the host tests cover. LED cues are
  awake-only. The buzzer uses the non-blocking path only.
- **0.2.0 contents, in this order of importance:**
  1. Holding both side keys goes Home from any screen (#5). The power button keeps its binding (sleep by default).
     This replaces the chord's second sleep path. It is the headline: the device stays usable when touch fails.
  2. LED and sound cues, each with a setting to turn it off: low battery, radio on, USB drive mode, and an optional
     key click. LED cues are on by default; sound is off by default.
  3. The device answers at `crossmono.local`, and its hotspot is `CrossMono-Reader` (#16).
  4. CrossPoint's tilt page turn is checked on the device, with no code.
- **Moved out of 0.2.0:**
  - The model badge on Home moves to 0.3.0, with the theme. Home's header title slot depends on the theme
    (`src/activities/home/HomeActivity.cpp:510-512`), the right-hand label was rejected in
    [0012](0012-boot-model-probe.md), and About already shows the model.
  - IMU rotation is left to CrossPoint. Rotation from the accelerometer helps every board with an IMU, and upstream
    is changing rotation now.
  - The RTC timer wake waits for the first feature that needs it, for example a reading timer that runs through
    sleep, or a scheduled sync. No 0.2.0 feature needs a wake. The real work then is the wake classification: today
    a cold boot on battery is read as a power-button wake (`lib/hal/HalGPIO.cpp:272-285`); telling it apart needs
    `bootWakeState().source`.
- **Upstream:**
  - Home from the keys: after the device test, a short CrossPoint PR text and patch for Nandan to post. The change
    is a PaperMono-only block, like the existing `FREEINK_DEVICE_PAPERMONO` blocks in `src/main.cpp`.
  - Cues: CrossPoint's `SCOPE.md` asks for a Discussion before a new feature. Once the cues have run on the device,
    we draft two paragraphs and Nandan opens it. Cues move to a `lib/hal` style only if CrossPoint wants them.
  - Driver glue for the LED, the buzzer and the RTC: nothing to offer, the SDK has it.
  - `crossmono.local`: ours only.
- This record replaces the "Cues and sensors (0.2.0)" section of 0008 and, for 0.2.0, its "Where drivers live"
  section. The NFC, LoRa, microphone and pin-glue parts of 0008 stand. It also moves "Home shows the model from
  0.2.0" in 0012 to 0.3.0.

## Consequences

- 0.2.0 adds no driver code. It adds two SDK libraries to the PaperMono environments, a cue module in `src/mono/`,
  and seams in `src/MappedInputManager.cpp` (new), `src/main.cpp`, `src/SettingsList.cpp`,
  `src/CrossPointSettings.h`, `lib/I18n/translations/english.yaml`, `platformio.ini` and the three network files for
  #16. Each seam row is added with its PR in [docs/upstream-sync.md](../upstream-sync.md).
- Holding both keys no longer sleeps the device. The release notes say so; the power button still does.
- Users who open `crosspoint.local` or look for the `CrossPoint-Reader` hotspot must use the new names. One release
  note line; there is no period with both names.
- LED, buzzer and RTC are on both models ([0003](0003-two-models.md)), so the cues should work on the Lite, but they
  are untested there ([0013](0013-lite-untested-at-0-1-0.md)).
- The roadmap's 0.2.0 section is rewritten, and its upstream line "offer stable driver glue (LED, buzzer, RTC wake)
  to the FreeInk SDK" is removed.

## Sources

- The files and lines cited above, at `3da343fd` (CrossPoint `42d58daa`, FreeInk SDK `5e94fe7`)
- CrossPoint PR #3820: https://github.com/crosspoint-reader/crosspoint-reader/pull/3820 (checked 2026-11-07)
- CrossPoint `develop` `e70e3f1a` (checked 2026-11-07): `src/main.cpp` unchanged since 2.0.0
- GitHub issues #4 (touch after wake), #5 (no button path to Home) and #16 (`crossmono.local`) in
  `nandanito/crossmono`
- The 0.2.0 plan, approved by Nandan on 2026-11-07
