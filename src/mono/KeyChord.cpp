#include "KeyChord.h"

#include <Arduino.h>
#include <BoardConfig.h>
#include <HalGPIO.h>

namespace mono {

void updateHomeChord(const HalGPIO& gpio) {
#if FREEINK_DEVICE_PAPERMONO
  // Read like the SDK reads them (InputManager::isDigitalPressed, which is private): active low.
  const auto down = [](const int8_t pin) { return pin >= 0 && digitalRead(pin) == LOW; };
  const auto& pins = BoardConfig::ACTIVE.input;
  const unsigned keys = (down(pins.up) ? KeyChord::KEY_UP : 0u) | (down(pins.down) ? KeyChord::KEY_DOWN : 0u);
  homeChord().update(gpio.isPressed(HalGPIO::BTN_POWER), keys, gpio.getPowerButtonHeldTime());
#else
  (void)gpio;
#endif
}

}  // namespace mono
