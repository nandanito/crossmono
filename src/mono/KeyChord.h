#pragma once

class HalGPIO;

// Holding both side keys goes Home (GitHub #5, ADR 0014).
//
// On the PaperMono the SDK reports two things as BTN_POWER (InputManager::updateDigitalTwoButton):
// - both side keys held: pressed once they have been down TWO_BUTTON_HOLD_MS (650 ms), with the held time counted
//   from when both went down, so it reads >= 650 ms from the first frame;
// - the PMIC power button: a one-tick pulse, pressed for one frame with a held time of about 0 ms.
// So a BTN_POWER held for 650 ms or more, with both keys down, is the chord. Both keys are checked as well because the
// SDK also backdates a PMIC click to the key press when one key is already held.
//
// Fingers rarely leave both keys in the same frame. When one key lifts first, the SDK starts a new gesture for the
// other key and reports Up or Down when it lifts, or Back or Confirm if it stays down 650 ms. So the chord keeps the
// keys until both are up, and one frame longer because our key read comes just after the SDK's.
namespace mono {

class KeyChord {
 public:
  // InputManager::TWO_BUTTON_HOLD_MS, which is private to the SDK.
  static constexpr unsigned long HOLD_MS = 650;

  // Side keys as read now: bit 0 for Up (KEY1), bit 1 for Down (KEY2).
  static constexpr unsigned KEY_UP = 1;
  static constexpr unsigned KEY_DOWN = 2;
  static constexpr unsigned BOTH_KEYS = KEY_UP | KEY_DOWN;

  // Call once per input frame, right after the button state is updated. Our key read comes just after the SDK's, so
  // "both down" also accepts the previous frame.
  void update(const bool powerHeld, const unsigned keys, const unsigned long powerHeldMs) {
    if (endsNow_) active_ = false;
    endsNow_ = false;
    const bool bothDown = keys == BOTH_KEYS || keysBefore_ == BOTH_KEYS;
    const bool chordHeld = powerHeld && powerHeldMs >= HOLD_MS && bothDown;
    pressedNow_ = chordHeld && !active_;
    if (chordHeld) active_ = true;
    if (active_ && keys == 0 && keysBefore_ == 0) endsNow_ = true;
    keysBefore_ = keys;
  }

  // The chord started in this frame: go Home.
  bool wasPressed() const { return pressedNow_; }
  // From the chord's start until both keys are up: no button event belongs to anything else.
  bool isActive() const { return active_; }

 private:
  bool pressedNow_ = false;
  bool active_ = false;
  bool endsNow_ = false;
  unsigned keysBefore_ = 0;
};

// The device's chord state. Constant-initialized, so no constructor or guard runs.
inline KeyChord& homeChord() {
  static KeyChord chord;
  return chord;
}

// Feeds homeChord() from the buttons. Call right after gpio.update(). Does nothing on other boards, so there the chord
// is never active.
void updateHomeChord(const HalGPIO& gpio);

}  // namespace mono
