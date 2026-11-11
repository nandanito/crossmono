#pragma once

namespace mono {

// The product name on the boot and sleep screens; a name, so not translated. tr(STR_CROSSPOINT) stays upstream's:
// the KOReader settings use it for CrossPoint's sync server.
inline constexpr char NAME[] = "CrossMono";

// Network names (GitHub #16, ADR 0014): mDNS answers at HOSTNAME.local, the hotspot is AP_SSID, and routers see
// DHCP_HOSTNAME_PREFIX plus the Wi-Fi MAC. The UDP discovery reply keeps CrossPoint's "crosspoint" token, which the
// Calibre plugin checks.
inline constexpr char HOSTNAME[] = "crossmono";
inline constexpr char AP_SSID[] = "CrossMono-Reader";
inline constexpr char DHCP_HOSTNAME_PREFIX[] = "CrossMono-Reader-";

}  // namespace mono
