#pragma once

class HalGPIO;

namespace mono {

// Starts input as gpio.begin() does. On the PaperMono it also works around two ways the
// SDK's touch bring-up fails at boot, which leaves touch off until a power cycle
// (GitHub #4). Other boards: gpio.begin() only.
void beginInput(HalGPIO& gpio);

}  // namespace mono
