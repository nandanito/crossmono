#pragma once

#include <cstdint>

namespace mono {

// ST25R3916 NFC reader on the full PaperMono (ADR 0012). Its IC identity register (0x3F) is read with the
// direct-read command 0x40 | 0x3F, as M5Stack's factory firmware does (M5PaperMono-UserDemo, hal_board.cpp).
constexpr uint8_t NFC_I2C_ADDRESS = 0x50;
constexpr uint8_t NFC_READ_IC_IDENTITY = 0x7F;
constexpr uint8_t ST25R3916_IC_TYPE = 0x05;

// Identity byte: bits [7:3] IC type, bits [2:0] revision.
constexpr uint8_t nfcIcType(const uint8_t identity) { return static_cast<uint8_t>(identity >> 3); }
constexpr uint8_t nfcIcRevision(const uint8_t identity) { return static_cast<uint8_t>(identity & 0x07); }

// An ST25R3916 has type 5 and a non-zero revision.
constexpr bool isSt25r3916(const uint8_t identity) {
  return nfcIcType(identity) == ST25R3916_IC_TYPE && nfcIcRevision(identity) != 0;
}

}  // namespace mono
