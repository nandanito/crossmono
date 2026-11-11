#include "Cues.h"

#include <BoardConfig.h>

#if FREEINK_DEVICE_PAPERMONO

#include <BatteryMonitor.h>
#include <Buzzer.h>
#include <HalGPIO.h>
#include <LedManager.h>
#include <Logging.h>
#include <M5Ioe1.h>
#include <M5Pm1.h>
#include <esp_timer.h>

#include <algorithm>

#include "CrossPointSettings.h"
#include "CuePolicy.h"
#include "activities/RenderLock.h"

namespace mono {

namespace {

constexpr unsigned long USB_POLL_MS = 1000;
constexpr unsigned long BATTERY_POLL_MS = 30000;

LedManager leds;
Buzzer buzzer;
LowBattery lowBattery;
Blink blink;
TonePlayer player;
bool ledsReady = false;
bool soundReady = false;
Leds shown;                  // what the LED shows now
unsigned playedSegment = 0;  // the TonePlayer segment the buzzer was last set for
esp_timer_handle_t toneTimer = nullptr;
bool onUsb = false;
uint8_t batteryPercent = 100;   // until the first good reading: no low-battery cue
uint8_t previousReading = 100;  // the cue uses the higher of the last two readings, so one sag cannot start it
bool batteryPolled = false;
bool usbPolled = false;
unsigned long usbPolledAt = 0;
unsigned long batteryPolledAt = 0;

LedColor colorOf(const Leds& legs) {
  return LedColor{static_cast<uint8_t>(legs.red ? 255 : 0), static_cast<uint8_t>(legs.green ? 255 : 0),
                  static_cast<uint8_t>(legs.blue ? 255 : 0)};
}

// Every I2C access here runs under the render lock. The SDK updates the IO expander's output register (green and
// blue legs, next to the panel reset and power) and the PM1's PWR_CFG (red leg) by unlocked read-modify-write, and
// the render task uses the same bus for the panel and the battery icon; Arduino's Wire also hands back read data
// after it has released its own lock. When the render task holds the lock, try again on the next pass. Drop the
// lock once the SDK serializes these accesses.

// What the legs really show. The SDK's LED writes do not report I2C failures, so each write is read back.
bool readLeds(Leds& legs) {
  uint8_t pwrCfg = 0;
  uint16_t out = 0;
  if (!freeink::m5pm1::readReg(freeink::m5pm1::REG_PWR_CFG, &pwrCfg) ||
      !freeink::m5ioe1::readReg16(freeink::m5ioe1::REG_GPIO_OUT_L, &out)) {
    return false;
  }
  legs = Leds{(pwrCfg & freeink::m5pm1::LED_R_EN) != 0, (out & freeink::m5ioe1::PIN_LED_GREEN) != 0,
              (out & freeink::m5ioe1::PIN_LED_BLUE) != 0};
  return true;
}

// Call with the render lock held. Updates `shown` to what the read-back saw; true when that is `legs`.
bool writeLeds(const Leds& legs) {
  leds.setAll(colorOf(legs));
  Leds actual;
  if (!readLeds(actual)) return false;  // unknown: `shown` stays different from `legs`, so the write is retried
  shown = actual;
  static bool mismatchLogged = false;
  if (actual != legs && !mismatchLogged) {
    mismatchLogged = true;  // once per boot: a leg that never reads back as written would retry on every pass
    LOG_ERR("MONO", "Cues: LED read-back %d%d%d, wrote %d%d%d (red green blue)", actual.red, actual.green, actual.blue,
            legs.red, legs.green, legs.blue);
  }
  return actual == legs;
}

void showLeds(const Leds& legs) {
  RenderLock lock(RenderLock::Mode::Try);
  if (lock.ownsLock()) writeLeds(legs);
}

// Ends a tone on time even while the main loop is busy (opening a book, saving to the SD card).
void silence(void*) { buzzer.noTone(); }

void sound(const uint16_t hz, const unsigned long ms) {
  if (toneTimer) esp_timer_stop(toneTimer);  // fails harmlessly when it is not running
  if (hz != 0 && toneTimer) {
    buzzer.tone(hz, 0);  // 0 ms: starts the tone without blocking
    esp_timer_start_once(toneTimer, static_cast<uint64_t>(ms) * 1000);
  } else {
    buzzer.noTone();
  }
}

}  // namespace

void beginCues() {
  RenderLock lock;  // see readLeds()
  ledsReady = leds.begin();
  // If the read-back fails, assume every leg is lit, so the first update writes the real state.
  if (ledsReady && !readLeds(shown)) shown = Leds{true, true, true};
  const bool buzzerReady = buzzer.begin();
  // One small allocation at boot, kept for the whole run.
  esp_timer_create_args_t timerArgs = {};
  timerArgs.callback = &silence;
  timerArgs.name = "mono_tone";
  if (esp_timer_create(&timerArgs, &toneTimer) != ESP_OK) {
    toneTimer = nullptr;
    LOG_ERR("MONO", "Cues: no tone timer, sound off");  // without it a tone could last as long as a busy loop pass
  }
  soundReady = buzzerReady && toneTimer != nullptr;
  LOG_INF("MONO", "Cues: LED %s, buzzer %s", ledsReady ? "ok" : "missing", buzzerReady ? "ok" : "missing");
}

void updateCues(const HalGPIO& gpio, const CueFrame& frame) {
  const unsigned long now = millis();

  const bool pollBattery = !batteryPolled || now - batteryPolledAt >= BATTERY_POLL_MS;
  const bool pollUsb = !usbPolled || now - usbPolledAt >= USB_POLL_MS;
  if (pollBattery || pollUsb) {
    RenderLock lock(RenderLock::Mode::Try);  // see readLeds(); a busy lock moves the poll to the next pass
    if (lock.ownsLock() && pollBattery) {
      static const BatteryMonitor battery;
      uint16_t percent = 0;
      if (battery.readPercentageChecked(percent)) {
        const auto reading = static_cast<uint8_t>(std::min<uint16_t>(percent, 100));
        batteryPercent = std::max(reading, previousReading);
        previousReading = reading;
      }
      batteryPolled = true;
      batteryPolledAt = now;
    }
    if (lock.ownsLock() && pollUsb) {
      onUsb = gpio.isUsbConnected();
      lowBattery.update(batteryPercent, onUsb);
      usbPolled = true;
      usbPolledAt = now;
    }
  }

  const uint8_t level = soundReady ? SETTINGS.sound : SOUND_OFF;
  float tapX = 0;
  float tapY = 0;
  const bool userInput = gpio.wasAnyPressed() || gpio.wasTouchTap(tapX, tapY);  // both only read the frame
  if (level != SOUND_OFF && lowBattery.takeAlert()) {
    player.play(LOW_BATTERY_ALERT, now);
  } else if (userInput && level == SOUND_ALERTS_AND_KEYS && !player.playing()) {
    player.play(KEY_CLICK, now);
  }
  if (level == SOUND_OFF) player.stop();
  const uint16_t hz = player.update(now);
  if (player.segment() != playedSegment) {
    playedSegment = player.segment();
    sound(hz, player.remainingMs(now));
  }

  if (!ledsReady) return;
  const bool enabled = SETTINGS.ledCues != 0;
  const bool red = blink.update(enabled && lowBattery.low(), now);
  const Leds wanted = ledsFor(enabled, red, frame.usbDrive, frame.radioOn);
  if (wanted != shown) showLeds(wanted);
  blink.shown(shown.red, now);  // every pass: a red leg that is already lit counts as the flash
}

void stopCues() {
  player.stop();
  playedSegment = player.segment();
  sound(0, 0);
  if (!ledsReady || shown == Leds{}) return;
  RenderLock lock;  // see readLeds()
  for (int attempt = 0; attempt < 3; ++attempt) {
    if (writeLeds(Leds{})) return;
  }
  LOG_ERR("MONO", "Cues: LED not confirmed off before sleep");
}

}  // namespace mono

#else

namespace mono {
void beginCues() {}
void updateCues(const HalGPIO&, const CueFrame&) {}
void stopCues() {}
}  // namespace mono

#endif
