#include "Model.h"

#include <BoardConfig.h>

#if FREEINK_DEVICE_PAPERMONO
#include <Arduino.h>
#include <Logging.h>
#include <M5Ioe1.h>
#include <M5Pm1.h>
#include <PaperMonoBoard.h>
#include <Wire.h>

#include <cstdio>

#include "CrossPointSettings.h"
#include "NfcIdentity.h"
#endif

namespace mono {

#if FREEINK_DEVICE_PAPERMONO
namespace {

namespace ioe1 = freeink::m5ioe1;
namespace pm1 = freeink::m5pm1;

// Radio pins (schematic V0.6.2). The SDK does not name them yet; on the Lite they are open nets.
// IO expander: register bit N is pin IO(N+1).
constexpr uint16_t IOE1_LORA_ANT_SW = 1u << 1;  // IO2  PYB_LoRa_ANT_SW
constexpr uint16_t IOE1_NFC_POWER = 1u << 3;    // IO4  PYB_NFC_EN
constexpr uint16_t IOE1_LORA_RESET = 1u << 9;   // IO10 PYB_LoRa_RST
constexpr uint16_t IOE1_RADIO_PINS = IOE1_LORA_ANT_SW | IOE1_NFC_POWER | IOE1_LORA_RESET;
// PMIC GPIO2 (PYG2_LoRa_EN). M5PM1 datasheet and m5stack/M5PM1: one bit per pin in MODE, OUT and DRV, a 2-bit
// field per pin in FUNC0 (00 = GPIO) and PULL0 (00 = no pull).
constexpr uint8_t PM1_LORA_POWER = 1u << 2;
constexpr uint8_t PM1_GPIO2_FIELD = 0x03u << 4;

// M5Stack's sequence: power, 50 ms, then up to five reads 20 ms apart.
constexpr unsigned long NFC_POWER_SETTLE_MS = 50;
constexpr int NFC_READ_ATTEMPTS = 5;
constexpr unsigned long NFC_READ_GAP_MS = 20;

bool nfcFound = false;  // written once in setup()

// Address probe first: on the Lite the address never answers, and a failed register read would log an error each
// time, a missed probe only at verbose level.
bool readNfcIdentity(uint8_t* identity) {
  Wire.beginTransmission(NFC_I2C_ADDRESS);
  if (Wire.endTransmission() != 0) return false;
  Wire.beginTransmission(NFC_I2C_ADDRESS);
  Wire.write(NFC_READ_IC_IDENTITY);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(NFC_I2C_ADDRESS, static_cast<uint8_t>(1)) != 1) return false;
  *identity = static_cast<uint8_t>(Wire.read());
  return true;
}

// The radio pins as push-pull outputs, low (NFC_EN, LoRa reset, antenna switch), as M5Stack's firmware holds NFC_EN.
// The SDK does not drive them, and the expander restarts with the PMIC on every wake with all pins as inputs.
bool holdExpanderRadioPinsLow() {
  return ioe1::updateReg16(ioe1::REG_GPIO_OUT_L, IOE1_RADIO_PINS, 0) &&
         ioe1::updateReg16(ioe1::REG_GPIO_PU_L, IOE1_RADIO_PINS, 0) &&
         ioe1::updateReg16(ioe1::REG_GPIO_PD_L, IOE1_RADIO_PINS, 0) &&
         ioe1::updateReg16(ioe1::REG_GPIO_DRV_L, IOE1_RADIO_PINS, 0) &&
         ioe1::updateReg16(ioe1::REG_GPIO_MODE_L, 0, IOE1_RADIO_PINS);
}

// LoRa power switch off. Level first, so the pin never drives high while it becomes an output.
bool holdLoRaPowerOff() {
  return pm1::updateReg(pm1::REG_GPIO_OUT, PM1_LORA_POWER, 0) &&
         pm1::updateReg(pm1::REG_GPIO_FUNC0, PM1_GPIO2_FIELD, 0) &&
         pm1::updateReg(pm1::REG_GPIO_PULL0, PM1_GPIO2_FIELD, 0) &&
         pm1::updateReg(pm1::REG_GPIO_DRV, PM1_LORA_POWER, 0) && pm1::updateReg(pm1::REG_GPIO_MODE, 0, PM1_LORA_POWER);
}

}  // namespace
#endif

void probeAtBoot() {
#if FREEINK_DEVICE_PAPERMONO
  const unsigned long start = millis();
  freeink::papermono::ensureBooted();  // already done by mono::beginInput(); cached

  const bool expanderOk = holdExpanderRadioPinsLow() && ioe1::write(IOE1_NFC_POWER, true);
  const unsigned long nfcPowerOn = millis();
  // The PMIC writes use the NFC settle time.
  const bool loraPowerOff = holdLoRaPowerOff();

  uint8_t identity = 0;
  bool answered = false;
  if (expanderOk) {
    const unsigned long settled = millis() - nfcPowerOn;
    if (settled < NFC_POWER_SETTLE_MS) delay(NFC_POWER_SETTLE_MS - settled);
    for (int attempt = 0; attempt < NFC_READ_ATTEMPTS && !nfcFound; ++attempt) {
      if (attempt > 0) delay(NFC_READ_GAP_MS);
      if (readNfcIdentity(&identity)) {
        answered = true;
        nfcFound = isSt25r3916(identity);
      }
    }
  }
  const bool nfcPowerOff = ioe1::write(IOE1_NFC_POWER, false);

  // Read back what the radio pins hold now, for the log and the hardware checklist.
  uint16_t ioOut = 0;
  uint16_t ioMode = 0;
  uint8_t pmOut = 0;
  uint8_t pmMode = 0;
  const bool readBack = ioe1::readReg16(ioe1::REG_GPIO_OUT_L, &ioOut) &&
                        ioe1::readReg16(ioe1::REG_GPIO_MODE_L, &ioMode) && pm1::readReg(pm1::REG_GPIO_OUT, &pmOut) &&
                        pm1::readReg(pm1::REG_GPIO_MODE, &pmMode);
  const bool radioPinsLow = expanderOk && nfcPowerOff && loraPowerOff && readBack && (ioOut & IOE1_RADIO_PINS) == 0 &&
                            (ioMode & IOE1_RADIO_PINS) == IOE1_RADIO_PINS && (pmOut & PM1_LORA_POWER) == 0 &&
                            (pmMode & PM1_LORA_POWER) != 0;
  const unsigned long elapsed = millis() - start;

  const char* verdict = modelName(nfcFound ? Model::PaperMono : Model::PaperMonoLite);
  char identityText[8] = "none";  // nothing answered at 0x50
  if (answered) {
    snprintf(identityText, sizeof(identityText), "0x%02X", identity);
  } else if (!expanderOk) {
    snprintf(identityText, sizeof(identityText), "skipped");  // expander write failed; no read tried
  }
  if (radioPinsLow) {
    LOG_INF(
        "MONO",
        "Model probe: NFC %s -> %s in %lu ms; radio pins low (IOE1 out 0x%04X mode 0x%04X, PM1 out 0x%02X mode 0x%02X)",
        identityText, verdict, elapsed, ioOut, ioMode, pmOut, pmMode);
  } else {
    LOG_ERR("MONO",
            "Model probe: NFC %s -> %s in %lu ms; radio pins NOT low (IOE1 out 0x%04X mode 0x%04X, PM1 out 0x%02X mode "
            "0x%02X)",
            identityText, verdict, elapsed, ioOut, ioMode, pmOut, pmMode);
  }
#endif
}

#if FREEINK_DEVICE_PAPERMONO
Model model() { return resolveModel(nfcFound, SETTINGS.modelOverride).model; }
ModelSource source() { return resolveModel(nfcFound, SETTINGS.modelOverride).source; }
const char* name() { return modelName(model()); }
#endif

}  // namespace mono
