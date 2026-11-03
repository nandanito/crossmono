#include "InputBringUp.h"

#include <HalGPIO.h>

#if FREEINK_DEVICE_PAPERMONO
#include <Arduino.h>
#include <Logging.h>
#include <M5Ioe1.h>
#include <M5Pm1.h>
#include <PaperMonoBoard.h>
#include <Wire.h>

#include <algorithm>
#include <iterator>
#endif

namespace mono {

#if FREEINK_DEVICE_PAPERMONO
namespace {

namespace ioe1 = freeink::m5ioe1;

constexpr unsigned long EXPANDER_WAIT_MS = 2000;
constexpr unsigned long EXPANDER_RETRY_MS = 25;
constexpr uint8_t EXPANDER_ADDRESSES[] = {ioe1::ADDR_PRIMARY, ioe1::ADDR_ALT};
constexpr int TOUCH_RETRIES = 2;

// The SDK's own presence check (m5ioe1::begin() reads the UID registers), behind an
// address-only probe: the core logs a failed register read, a missed probe only at
// verbose level, so polling stays quiet.
bool expanderAnswers(const uint8_t addr) {
  Wire.beginTransmission(addr);
  if (Wire.endTransmission() != 0) return false;
  uint8_t uid[2] = {0, 0};
  return ioe1::readBytesAt(addr, ioe1::REG_UID_L, uid, sizeof(uid));
}

// Seen after a PMIC restart: the expander did not answer the SDK's single probe, and the
// SDK then treats it as absent for the session, so the touch rail stays off. A retry
// cannot undo that, so wait before the SDK's bring-up.
void waitForExpander() {
  freeink::m5pm1::beginBus();  // starts Wire on the shared bus; the SDK repeats it harmlessly
  const unsigned long start = millis();
  const uint8_t* found = std::end(EXPANDER_ADDRESSES);
  int attempts = 0;
  while (found == std::end(EXPANDER_ADDRESSES) && millis() - start < EXPANDER_WAIT_MS) {
    if (attempts++ > 0) delay(EXPANDER_RETRY_MS);
    found = std::find_if(std::begin(EXPANDER_ADDRESSES), std::end(EXPANDER_ADDRESSES), expanderAnswers);
  }
  const unsigned long elapsed = millis() - start;
  if (found == std::end(EXPANDER_ADDRESSES)) {
    LOG_ERR("MONO", "IO expander not ready after %lu ms", elapsed);
  } else if (attempts > 1) {
    LOG_INF("MONO", "IO expander 0x%02X ready after %lu ms (%d attempts)", *found, elapsed, attempts);
  } else {
    LOG_DBG("MONO", "IO expander 0x%02X ready", *found);
  }
}

}  // namespace
#endif

void beginInput(HalGPIO& gpio) {
#if FREEINK_DEVICE_PAPERMONO
  waitForExpander();
#endif
  gpio.begin();
#if FREEINK_DEVICE_PAPERMONO
  // Both models have touch. Seen on the device: the first bring-up left the controller in
  // reset (expander OUT 0x1000: rail on, reset low; one expander read failed during that
  // step). A second pass, with the rail already on, released it each time.
  for (int retry = 1; retry <= TOUCH_RETRIES && !gpio.hasTouch(); ++retry) {
    LOG_INF("MONO", "No touch controller found, starting input again (%d of %d)", retry, TOUCH_RETRIES);
    gpio.begin();
  }
  if (!gpio.hasTouch()) {
    // "failed" means the SDK's one-time expander setup failed, which a retry cannot redo.
    LOG_ERR("MONO", "Touch controller still not found (expander setup %s)",
            freeink::papermono::ensureBooted() ? "ok" : "failed");
  }
#endif
}

}  // namespace mono
