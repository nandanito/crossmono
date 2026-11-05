# Security policy

## Reporting a problem

Please do not report a security problem in a public issue or discussion.

Report it privately on GitHub: open the repository's **Security** tab and choose **Report a vulnerability**, or go
straight to https://github.com/nandanito/crossmono/security/advisories/new. Only you and the maintainer see the
report.

Please include:

- the CrossMono version (Settings → System → About) and the model;
- what an attacker can do, and what they need for it (the same Wi-Fi network, a Bluetooth connection, a file on
  the SD card, the device in hand…);
- the steps to reproduce it.

CrossMono has one volunteer maintainer, so an answer can take a few days. The answer comes in the private report.
When the problem is fixed, the published advisory credits you, unless you prefer not to be named.

## Supported versions

CrossMono is before 1.0. Fixes go into the next release only; older versions get no fixes. Update over Wi-Fi
(Settings → System → Check for Updates) or install the latest release ([docs/install.md](docs/install.md)).

## CrossPoint and the FreeInk SDK

Most of CrossMono's code comes from [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader)
and the [FreeInk SDK](https://github.com/Free-Ink/freeink-sdk). If the problem is in their code, report it to us
anyway: we tell you whether it also affects them and where to report it there.

## Known limits

These are how the device and CrossPoint work today, not vulnerabilities:

- The device has no secure boot and no flash encryption. Anyone who has the device and a USB cable can read or
  replace its firmware.
- The web server for file transfer has no password. Anyone on the same network can use it while it runs (see
  [docs/webserver.md](docs/webserver.md)). Use it only on networks you trust.
