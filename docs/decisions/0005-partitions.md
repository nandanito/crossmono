# 0005. Partition table

- Status: Accepted
- Date: 2026-10-28

## Context

The PaperMono has 16 MB of flash. CrossPoint's `partitions.csv` gives each app slot 0x640000 (6,553,600 B) and
keeps a 0x360000 (3.375 MB) `spiffs` partition that nothing mounts. The `coredump` partition is present but unused.

Image sizes for the PaperMono:

| Build | Size |
|---|---|
| CrossPoint `1.6.5` release asset | 5,639,376 B |
| CrossPoint `2.0.0rc` release asset | 5,370,912 B |
| `pio run -e papermono-gh_release` at the bootstrap base, measured 2026-10-29 | **5,360,752 B** (`firmware.bin`; PlatformIO reports 5,355,486 B = 81.7 % of 6,553,600) |
| CrossNext dev build on the PaperMono | 7,670,640 B |

The CrossNext number shows how fast features fill the upstream slot: it no longer fits. CrossPlay (and the
CrossNext PaperMono port) already removed `spiffs` and gave the space to the app slots. Its host test
(`host-tests/release/run.sh`) checks the table.

OTA writes only an app slot and `otadata`, never the partition table at 0x8000. A device keeps the table it was
last flashed with over USB. CrossPoint's OTA starts with `esp_ota_begin(..., OTA_SIZE_UNKNOWN, ...)`
(`src/network/OtaUpdater.cpp:156`), so it does not check the image size before writing.

## Options considered

1. **Keep CrossPoint's table.** CrossPoint users could switch to CrossMono through CrossPoint's own updater or SD
   flasher without a USB flash. But we start at 82 % of the slot, near the warning line, with all hardware features
   still to come.
2. **CrossPlay's table** (chosen). 8,323,072 B per slot; the base image uses 64.4 %. The table is already used on
   PaperMono hardware and has a host test.
3. **A custom table with a filesystem partition.** Nothing needs one: books, fonts, settings and caches are on the
   SD card.

## Decision

CrossPlay's layout, copied exactly:

```csv
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,  0x5000,
otadata,  data, ota,     0xe000,  0x2000,
app0,     app,  ota_0,   0x10000, 0x7F0000,
app1,     app,  ota_1,   0x800000,0x7F0000,
coredump, data, coredump,0xFF0000,0x10000,
```

- No `spiffs`.
- A host test asserts this table (offsets 64 KB aligned, no overlap, end at 0x1000000, equal app slots, no
  `spiffs`).
- CI gates the app image size against the slot: warning at 85 % (7,074,611 B), failure at 95 % (7,906,918 B).
- The first install of CrossMono is always a full flash of the merged image at 0x0.

## Consequences

- A device coming from stock firmware or from CrossPoint needs one USB install. OTA and CrossPoint's SD flasher
  cannot change the table. The install docs and the web flasher handle this ([0009](0009-install.md)).
- The table becomes a seam: `partitions.csv` is edited, so every upstream sync must check it
  ([docs/upstream-sync.md](../upstream-sync.md)).
- The base image leaves 2,962,320 B free in the slot, of which 1,713,859 B are below the 85 % warning line.
- An OTA image larger than the slot fails only during the write. CrossNext adds an explicit size check
  (`TOO_LARGE_ERROR`, `CrossNext-PaperMono/src/network/OtaUpdater.cpp:170-180`); consider the same check when the
  OTA source is changed in 0.1.0.

## Sources

- `partitions.csv` at `60d3c8bb`; `src/network/OtaUpdater.cpp:156`
- CrossNext-PaperMono `partitions.csv` (CrossPlay layout with its reasoning), `host-tests/release/run.sh`
- Release assets: https://github.com/crosspoint-reader/crosspoint-reader/releases
- Local build: `~/.local/bin/pio run -e papermono-gh_release`, PlatformIO Core 6.2.0, 2026-10-29
- ESP-IDF partition tables: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/partition-tables.html

## Addendum 2026-10-29: the table file

The layout above is unchanged. It lives in its own file, `partitions_papermono.csv`, and the three PaperMono
environments in `platformio.ini` point at it with `board_build.partitions`, the same way upstream's Picco
environments use `partitions_picco.csv`. Upstream's `partitions.csv` is not edited. This replaces the Consequences
bullet that says `partitions.csv` is edited: the seam is the `board_build.partitions` line in each PaperMono
environment, and `test/mono/test_partitions.py` fails if a sync drops one.

The checks are `scripts/mono/partitions.py` (table rules, used by the host test) and `scripts/mono/size_gate.py`
(the gate, run by CI after each build). Two details of the Decision, stated exactly:

- Only app offsets must be 64 KB aligned; data offsets need 4 KB (`nvs` is at 0x9000).
- The gate compares the exact percentage: it warns from 7,074,612 B (85 %) and fails from 7,906,919 B (95 %).

A full flash of the merged image fills NVS (0x9000-0xDFFF) with 0xFF, so it erases the device secret and BLE
pairings; settings on the SD card stay. A developer's `pio run -t upload` also writes the table (with the
bootloader, a reset otadata and the app) and keeps NVS. The released install path stays the full flash.

Erratum to the Context: the `coredump` partition is used. The prebuilt Arduino sdkconfig for this board writes core
dumps to flash (`CONFIG_ESP_COREDUMP_ENABLE_TO_FLASH`), so the table keeps it.

## Addendum 2026-11-04: OTA size check

The Consequences bullet on the OTA size check is done. `OtaUpdater::installUpdate()` compares the asset size from
the release JSON with the update slot before `esp_ota_begin()` erases it, and the screen shows "Firmware too large
for partition" (`TOO_LARGE_ERROR`). The seam is listed in [docs/upstream-sync.md](../upstream-sync.md); the check is
offered to CrossPoint.

## Erratum 2026-11-05: the size check upstream

The 2026-11-04 addendum says the OTA size check "is offered to CrossPoint". It was not offered. It is on hold: we
carry it, and offer it when CrossPoint's image nears its slot or the seam conflicts at a sync
([docs/upstream-sync.md](../upstream-sync.md), `src/network/OtaUpdater.cpp` row).
