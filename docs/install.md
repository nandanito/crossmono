# Installing CrossMono

The quickest way is the install page, **https://crossmono.github.io**. This page explains the same steps in more
detail, the esptool command for computers without a supported browser, and what to know when you come from
CrossPoint.

The first install of CrossMono is always over USB. After that, CrossMono updates itself over Wi-Fi.

## What you need

- A PaperMono or PaperMono-Lite. CrossMono is one firmware for both.
- A USB-C cable that carries data. Some cables only charge.
- A computer with **Chrome** or **Edge**. They have Web Serial, which the install page needs.
  - Firefox 151 or newer has Web Serial on desktop too, but it has not been tested with CrossMono. Mozilla says
    Firefox first asks you to add a small "site permission add-on" for the page.
  - Safari, phones and tablets cannot install. Use another computer, or esptool ([below](#install-with-esptool)).
  - On Linux, your user may need to be in the `dialout` group to use the serial port.

## What a USB install erases

A USB install erases the device's internal memory. You lose:

- **the Bluetooth pairings.** Pair your remote again after the install.
- **the keys of protected books.** LCP loans brought over from CrossPoint cannot be unlocked again on CrossMono.

Your books, settings and Wi-Fi networks are on the SD card, and they stay. Updates over Wi-Fi erase nothing.

## SD card: MBR only

CrossMono reads only SD cards with an **MBR** partition table, from the first partition, formatted as FAT32 or
exFAT. It cannot read a card formatted with GPT. Most cards come with MBR.

If CrossMono shows no card, copy your books off it, then reformat it with MBR. Formatting erases the card.

- **Windows or Mac:** the SD Association's [SD Card Formatter](https://www.sdcard.org/downloads/formatter/).
- **Mac, Disk Utility:** View → Show All Devices, select the card (the device, not the volume under it), Erase,
  Format: MS-DOS (FAT) or ExFAT, Scheme: Master Boot Record.
- **Linux, GNOME Disks:** select the card, ⋮ → Format Disk, Partitioning: "Compatible with all systems and devices
  (MBR / DOS)", then create one FAT or exFAT partition.

## Install from the browser

1. **Wake the PaperMono and keep it awake.** A sleeping device does not show up on USB. If it is in USB drive mode,
   leave that mode first.
2. Connect it to the computer with the USB-C cable.
3. Open https://crossmono.github.io in Chrome or Edge and click the install button.
4. Choose the device in the browser's list. It is usually called **"USB JTAG/serial debug unit"**. On a Mac it
   showed as "USB JTAG/serial debug unit (cu.usbmodem2101)"; the part in brackets depends on your computer.
5. Click **Install CrossMono**, then **Install**. The browser erases the device and writes CrossMono. This takes a
   few minutes. Keep the cable connected.
6. When the browser shows "Installation complete!", the device restarts into CrossMono.

If the device is not in the list, check that it is awake, then try another cable or another USB port.

The page also offers a **test build** when a release candidate is out. Test builds are for testers and may have
bugs. Updates over Wi-Fi do not offer them; install the next one from the page.

## Install with esptool

Without a supported browser, use Espressif's [esptool](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/)
(Python 3):

```sh
pip install esptool
```

1. From the [release page](https://github.com/nandanito/crossmono/releases), download
   `crossmono-<version>-papermono-full.bin` and `SHA256SUMS` into one folder.
2. Check the download in that folder. `SHA256SUMS` also lists files you did not download, so tell the check to skip
   them:

   ```sh
   sha256sum -c --ignore-missing SHA256SUMS          # Linux
   shasum -a 256 -c --ignore-missing SHA256SUMS      # macOS
   ```

   The line for the full image must say `OK`.
3. Wake the device and connect it (steps 1 and 2 above).
4. Write the full image at offset 0x0:

   ```sh
   esptool --chip esp32s3 write-flash 0x0 crossmono-<version>-papermono-full.bin
   ```

   esptool 4 spells the command `write_flash`. esptool finds the port by itself; if it picks the wrong one, add
   `--port <port>` (for example `/dev/ttyACM0` on Linux, `/dev/cu.usbmodem2101` on a Mac, `COM3` on Windows).
5. esptool restarts the device when it is done.

Like the browser install, this erases the Bluetooth pairings and the keys of protected books.

Use the **full** image, at **0x0**. The other `.bin` on the release page is the update image for an app slot; it
does not contain the partition table and does not work as a first install.

## Updates

After the first install, CrossMono updates itself over Wi-Fi: Settings → System → Check for Updates. Updates erase
nothing. They offer only final releases, not test builds.

## Coming from CrossPoint

CrossMono uses its own partition table, with larger app slots than CrossPoint's. Only a USB install writes the
partition table, so:

- Install CrossMono from the install page or with esptool, as above.
- Do not install CrossMono with CrossPoint's own update paths. CrossPoint's update over Wi-Fi never offers
  CrossMono, and its **SD Card Firmware Update** with a CrossMono `.bin` would keep CrossPoint's partition table.

CrossMono uses the same `.crosspoint` folder on the SD card, so your books, settings, reading progress and Wi-Fi
networks stay. What the install erases is listed [above](#what-a-usb-install-erases).

## Coming from M5Stack's firmware

The install is the same. If you may want M5Stack's firmware back later, save a copy of the whole flash first. This
reads 16 MB and takes a few minutes:

```sh
esptool --chip esp32s3 read-flash 0 0x1000000 papermono-backup.bin
```

To restore it later: `esptool --chip esp32s3 write-flash 0x0 papermono-backup.bin`. A way back to CrossPoint with
CrossPoint's own installer has not been tested yet.
