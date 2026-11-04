#pragma once

#include <cstddef>
#include <cstdio>

// The GitHub release the updater reads (ADR 0009). releases/latest never returns a pre-release; to test OTA with a
// candidate, point a local build at its tag with build_src_flags in platformio.local.ini (RELEASING.md):
//   -DCROSSMONO_OTA_RELEASE_URL=\"https://api.github.com/repos/nandanito/crossmono/releases/tags/0.1.0-rc.1\"
#ifndef CROSSMONO_OTA_RELEASE_URL
#define CROSSMONO_OTA_RELEASE_URL "https://api.github.com/repos/nandanito/crossmono/releases/latest"
#endif

namespace mono {

// Writes the OTA asset name "crossmono-<tag><suffix>.bin"; `suffix` is "-<board tag>". When the name does not fit,
// returns false and leaves `out` empty, so it matches no asset instead of a truncated one.
inline bool formatAssetName(char* out, const size_t outSize, const char* tag, const char* suffix) {
  if (outSize == 0) return false;
  const int len = snprintf(out, outSize, "crossmono-%s%s.bin", tag, suffix);
  if (len < 0 || static_cast<size_t>(len) >= outSize) {
    out[0] = '\0';
    return false;
  }
  return true;
}

}  // namespace mono
