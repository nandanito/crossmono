#pragma once

class HalGPIO;

// LED and sound cues on the PaperMono (ADR 0014); the rules are in mono/CuePolicy.h. Other boards get empty bodies.
namespace mono {

// What the main loop already knows in this pass.
struct CueFrame {
  bool radioOn;   // Wi-Fi in use
  bool usbDrive;  // USB drive mode
};

// Call once in setup(), after the settings are loaded and mono::beginInput() has brought up the IO expander.
void beginCues();
// Call on every loop pass, before the USB drive mode early return.
void updateCues(const HalGPIO& gpio, const CueFrame& frame);
// Call before sleep: the IO expander stays powered and would keep the green and blue legs lit.
void stopCues();

}  // namespace mono
