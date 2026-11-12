#pragma once

// Keeps a power-button release for the main loop (GitHub #25).
//
// On the PaperMono a power-button click is a one-tick BTN_POWER pulse: pressed in one input update, released in the
// next (KeyChord.h). Screens that block in a transfer read input themselves with MappedInputManager::update(true), so
// the release often lands in one of their updates, where the main loop's sleep, Force Refresh and Power as Confirm
// checks cannot see it. update(true) already keeps Home-key and power-click actions for the next main-loop pass
// (deferredHomeAction); this keeps the release itself.
namespace mono {

class PowerRelease {
 public:
  // Call once per input update. `deferred`: the update is a blocking loop's update(true). `released`: the power
  // button was released in this update.
  void update(const bool deferred, const bool released) {
    if (deferred) {
      pending_ = pending_ || released;
      reportNow_ = false;
      return;
    }
    reportNow_ = pending_;
    pending_ = false;
  }

  // True for the one main-loop update after a release that an update(true) saw.
  bool wasReleased() const { return reportNow_; }

  // Drops a release that has not been reported yet. Called when the screen changes.
  void forget() { pending_ = false; }

 private:
  bool pending_ = false;
  bool reportNow_ = false;
};

// The device's release state. Constant-initialized, so no constructor or guard runs.
inline PowerRelease& powerRelease() {
  static PowerRelease release;
  return release;
}

}  // namespace mono
