# 0006. Removing upstream features

- Status: Accepted
- Date: 2026-10-28

## Context

CrossPoint is built for many boards (X3/X4, X4 Pro, Sticky, PaperMono, Metalio, EEGO A4, Picco) and links features
the PaperMono may not need. Its `[base]` build flags include `EINK_DISPLAY_SINGLE_BUFFER_MODE=1`
(`platformio.ini:42`), wolfSSL with TLS 1.3 (`platformio.ini:98`), and the `[ble_page_turner]` group
(`platformio.ini:39`, defined at 261) with `FREEINK_CAP_BLE_HID_HOST=1` for Bluetooth keyboards and page turners. The PaperMono environment adds USB mass
storage (`FREEINK_CAP_USB_MSC=1`). The SDK's Microphone, Buzzer and LedManager libraries are not used by CrossPoint.

With the partition table from [0005](0005-partitions.md), the base image uses 64.4 % of an app slot, so there is
no size pressure today. Every deleted upstream file would turn into a merge conflict whenever upstream touches it.

CrossPoint ships `scripts/firmware_size_history.py` for size measurements.

## Options considered

1. **Delete code we do not need** (other boards, unused features). Smaller tree, but every upstream sync conflicts
   on the deleted files, and our diff hides the changes that matter.
2. **Switch features off with build flags, `lib_deps` and environment choice** (chosen). Upstream files stay as
   they are; switching a feature off is a one-line change in our environment.
3. **Keep everything forever.** Fine today, but the hardware features will need space later.

## Decision

- Features are removed only with build flags, `lib_deps`, environment choice and documentation. Upstream files are
  never deleted.
- Nothing is removed in 0.1.0.
- Before cutting any feature, measure what it costs (`scripts/firmware_size_history.py` or a with/without build)
  and record the number in the PR.

## Consequences

- Code for other boards stays in the tree. Our CI builds only our own environments ([0010](0010-quality-and-ci.md)).
- Turning a feature off may need a small seam where upstream lacks a flag. Such seams are listed in
  [docs/upstream-sync.md](../upstream-sync.md), and a flag is offered upstream when it is useful to others.

## Sources

- `platformio.ini:9-187` (`[base]`), `:261-286` (`[ble_page_turner]`), `:571-589` (`[env:papermono]`) at `60d3c8bb`
- `scripts/firmware_size_history.py`
- [0005](0005-partitions.md) (image size measurements)
