#pragma once

#include <cstdint>

// LED and sound cues (ADR 0014): what the RGB LED and the buzzer should do. Pure, so the host tests cover it; the
// hardware side is mono/Cues.cpp.
namespace mono {

// Values of CrossPointSettings::sound.
constexpr uint8_t SOUND_OFF = 0;
constexpr uint8_t SOUND_ALERTS = 1;
constexpr uint8_t SOUND_ALERTS_AND_KEYS = 2;

// A local test build can raise the threshold to try the cue on a charged battery (docs/hardware-test-checklist.md).
#ifndef CROSSMONO_LOW_BATTERY_PERCENT
#define CROSSMONO_LOW_BATTERY_PERCENT 10
#endif
constexpr uint8_t LOW_BATTERY_PERCENT = CROSSMONO_LOW_BATTERY_PERCENT;  // the cue starts at or below this
// It stops at or above this, so a noisy reading does not make it flicker.
constexpr uint8_t LOW_BATTERY_CLEAR_PERCENT = LOW_BATTERY_PERCENT + 3;
constexpr unsigned long LOW_BATTERY_BLINK_PERIOD_MS = 30000;
constexpr unsigned long LOW_BATTERY_BLINK_ON_MS = 120;

// Low battery: on battery power and at or below LOW_BATTERY_PERCENT. The alert sound plays once per boot.
class LowBattery {
 public:
  void update(const uint8_t percent, const bool onUsb) {
    if (!low_ && !onUsb && percent <= LOW_BATTERY_PERCENT) {
      low_ = true;
      if (!alerted_) alertPending_ = alerted_ = true;
    } else if (low_ && (onUsb || percent >= LOW_BATTERY_CLEAR_PERCENT)) {
      low_ = false;
      alertPending_ = false;  // an alert held back (Sound Off) must not play once the battery is fine again
    }
  }
  bool low() const { return low_; }
  // True once, the first time the battery is low in this boot, while it is still low.
  bool takeAlert() {
    const bool alert = alertPending_;
    alertPending_ = false;
    return alert;
  }

 private:
  bool low_ = false;
  bool alerted_ = false;
  bool alertPending_ = false;
};

// One leg per cue: red blinks for low battery, green is USB drive mode, blue is a radio (Wi-Fi) in use.
struct Leds {
  bool red = false;
  bool green = false;
  bool blue = false;
  bool operator==(const Leds& other) const { return red == other.red && green == other.green && blue == other.blue; }
  bool operator!=(const Leds& other) const { return !(*this == other); }
};

constexpr Leds ledsFor(const bool enabled, const bool redLit, const bool usbDrive, const bool radioOn) {
  if (!enabled) return Leds{};
  return Leds{redLit, usbDrive, radioOn};
}

// The low-battery flash. A flash that is due waits until the LED really shows it (the write can be put off while the
// render task is busy), then lasts LOW_BATTERY_BLINK_ON_MS from that moment; the next one is due a period later.
class Blink {
 public:
  // Whether the red leg should be lit at nowMs.
  bool update(const bool active, const unsigned long nowMs) {
    if (!active) {
      lit_ = false;
      offPending_ = false;
      due_ = true;  // the first flash comes at once
      return false;
    }
    if (lit_ && nowMs - litAt_ >= LOW_BATTERY_BLINK_ON_MS) {
      lit_ = false;
      offPending_ = true;
      nextAt_ = litAt_ + LOW_BATTERY_BLINK_PERIOD_MS;
    }
    // The next flash waits for the LED to have shown this one's end, even after a stall longer than a period.
    if (!lit_ && !due_ && !offPending_ && static_cast<long>(nowMs - nextAt_) >= 0) due_ = true;
    return lit_ || due_;
  }
  // Call on every pass with what the LED really shows.
  void shown(const bool redLit, const unsigned long nowMs) {
    if (!redLit) {
      offPending_ = false;
      return;
    }
    if (!due_) return;
    due_ = false;
    lit_ = true;
    litAt_ = nowMs;
  }

 private:
  bool due_ = true;
  bool lit_ = false;
  bool offPending_ = false;
  unsigned long litAt_ = 0;
  unsigned long nextAt_ = 0;
};

struct Tone {
  uint16_t hz;  // 0 = silence
  uint16_t ms;
};

constexpr Tone KEY_CLICK[] = {{3000, 15}};
constexpr Tone LOW_BATTERY_ALERT[] = {{2000, 80}, {0, 100}, {2000, 80}};

// Plays a short tone sequence without blocking: update() says which frequency should sound now.
class TonePlayer {
 public:
  template <unsigned N>
  void play(const Tone (&tones)[N], const unsigned long nowMs) {
    tones_ = tones;
    count_ = N;
    index_ = 0;
    startedAt_ = nowMs;
    ++segment_;
  }
  bool playing() const { return index_ < count_; }
  void stop() {
    if (!playing()) return;
    index_ = count_ = 0;
    ++segment_;
  }
  // Changes whenever a new tone or gap starts, so the caller starts each one once, even if it has the same
  // frequency as the one before.
  unsigned segment() const { return segment_; }
  // How long the current tone or gap still lasts at nowMs, after update(nowMs).
  unsigned long remainingMs(const unsigned long nowMs) const {
    return index_ < count_ ? tones_[index_].ms - (nowMs - startedAt_) : 0;
  }
  // The frequency to sound at nowMs, 0 when silent.
  uint16_t update(const unsigned long nowMs) {
    while (index_ < count_ && nowMs - startedAt_ >= tones_[index_].ms) {
      startedAt_ += tones_[index_].ms;
      ++index_;
      ++segment_;
    }
    return index_ < count_ ? tones_[index_].hz : 0;
  }

 private:
  const Tone* tones_ = nullptr;
  unsigned count_ = 0;
  unsigned index_ = 0;
  unsigned long startedAt_ = 0;
  unsigned segment_ = 0;
};

}  // namespace mono
