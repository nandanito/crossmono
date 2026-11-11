# CrossMono

Reading-first, open-source firmware for the M5Stack **PaperMono** and **PaperMono-Lite** e-paper devices. It is
built on [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader) and the
[FreeInk SDK](https://github.com/Free-Ink/freeink-sdk).

> **Status: pre-1.0.** CrossMono is new. Version 0.1.0 is CrossPoint Reader 2.0.0 for the PaperMono, with
> CrossMono's name, updates and install. Expect rough edges, and please [report them](#help-and-feedback).

## What it is

CrossPoint Reader is community-built e-reader firmware: EPUB, TXT and XTC books, custom fonts, highlights,
dictionaries, KOReader sync, Wi-Fi file transfer, OPDS catalogs and much more. It already runs on the PaperMono.

CrossMono is CrossPoint made for this one device. In 0.1.0 it adds:

- **One firmware for both models**, which detects the model when it starts.
- **More room for features**: two app slots of 7.9 MiB each, instead of CrossPoint's 6.25 MiB.
- **Updates over Wi-Fi from CrossMono's own releases.**
- **An install page** at https://crossmono.github.io.

Later versions use the PaperMono hardware that CrossPoint leaves unused: LEDs, buzzer, motion sensor, timer wake,
NFC, LoRa and the microphone ([roadmap](../docs/roadmap.md)). Reading stays first.

## Both models, one firmware

| | PaperMono | PaperMono-Lite |
|---|---|---|
| Reading, Wi-Fi, Bluetooth page turners, touch, frontlight | yes | yes |
| NFC and LoRa radios | yes (not used yet) | no |
| CrossMono firmware | the same file | the same file |

CrossMono reads the NFC chip's identity when it starts; a device without one is a PaperMono-Lite. About (Settings →
System → About) shows the result, for example "PaperMono (detected)". If it is wrong, choose the model under
Settings → System → Model.

**The Lite has not been tested yet**, because we do not have one. If you have one, please save a backup of the flash
first ([install docs](../docs/install.md#coming-from-m5stacks-firmware)), try CrossMono and tell us how it went in an
[issue](https://github.com/nandanito/crossmono/issues/new/choose) or a
[discussion](https://github.com/nandanito/crossmono/discussions).

## Install

You need Chrome, Edge or Brave on a computer, and a USB-C cable that carries data.

1. Wake the PaperMono and connect it to the computer. A sleeping device does not show up.
2. Open **https://crossmono.github.io** and click the install button.
3. Choose the device ("USB JTAG/serial debug unit") and confirm. Keep the cable connected until the page says
   "Installation complete!".

The first install erases the device's internal memory: Bluetooth pairings and the keys of protected books. Your
books, settings and Wi-Fi networks are on the SD card, and they stay. The SD card must use MBR, not GPT.

[docs/install.md](../docs/install.md) has the details: the esptool command for other systems, the SD card, and
what to know when you come from CrossPoint.

After the first install, CrossMono updates itself over Wi-Fi: Settings → System → Check for Updates. Updates erase
nothing.

## Using CrossMono

CrossMono works like CrossPoint, so [CrossPoint's user guide](../USER_GUIDE.md) applies. It is written for all
CrossPoint devices. On CrossMono:

- **Keys.** The PaperMono has two keys and a touch screen. A short press on a key moves up or down. Holding one
  key for a little over half a second is Back or Confirm. Holding both keys for the same time goes Home from any
  screen. The power button puts the device to sleep, or does what Settings → Controls → Short Power Button Click
  is set to.
- **Name and logo.** The boot and sleep screens, About and the web interface show CrossMono where the guide says
  CrossPoint.
- **Model.** Settings → System → Model, and the Model row in About, are CrossMono's.
- **Cues.** The LED shows blue while Wi-Fi is on and green in USB drive mode, and flashes red every 30 s when the
  device runs on battery at 10 % or below. Settings → System → LED Cues turns it off. Settings → Controls → Sound
  can add a double beep, once per start, when the battery gets low, and a click for each key press and tap; it is
  Off by default. The LED cannot light
  while the device sleeps. The Lite has the same LED and buzzer, but nobody has tested the cues on it yet.
- **About** also shows the CrossPoint version and the FreeInk SDK commit that this CrossMono is built on.
- **Updates** come from CrossMono's releases, not CrossPoint's.
- **Network names.** The web interface answers at `http://crossmono.local/`, the hotspot is `CrossMono-Reader`,
  and routers list the device as `CrossMono-Reader-` and its Wi-Fi address. CrossPoint's guide and docs
  say `crosspoint.local` and `CrossPoint-Reader`.
- **Names that stay CrossPoint's**: the `.crosspoint` folder on the SD card. It holds the settings and reading
  state, so they carry over between CrossPoint and CrossMono, and CrossPoint's plugins use it.

Known problems are in the [issues](https://github.com/nandanito/crossmono/issues). For example, some on-screen
buttons can be reached only by touch.

## Help and feedback

- **Bugs:** [open an issue](https://github.com/nandanito/crossmono/issues/new/choose).
- **Questions and ideas:** [discussions](https://github.com/nandanito/crossmono/discussions).
- **Security problems:** see [SECURITY.md](../SECURITY.md). Do not report them in public.
- **Contributing:** see [CONTRIBUTING.md](../CONTRIBUTING.md). Changes that help every CrossPoint device belong in
  [CrossPoint](https://github.com/crosspoint-reader/crosspoint-reader).

Versions are explained in [VERSIONING.md](../VERSIONING.md), changes in [CHANGELOG.md](../CHANGELOG.md), and the
project's decisions in [docs/decisions/](../docs/decisions/README.md).

## Credits

Almost all of CrossMono is the work of others:

- [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader) and its contributors: the reader, the
  interface, the web tools.
- The [FreeInk SDK](https://github.com/Free-Ink/freeink-sdk): the board support and drivers for the PaperMono.
- The libraries, fonts and data listed in [THIRD-PARTY-NOTICES](../THIRD-PARTY-NOTICES).

## Licence

CrossPoint's code and CrossMono's own code are under the [MIT licence](../LICENSE). The firmware image also
contains third-party code under other licences. Because it includes wolfSSL, the firmware image as a whole is
distributed under the GNU General Public License, version 3. CrossPoint states the same for its firmware. Details,
and how to get the source of a release: [THIRD-PARTY-NOTICES](../THIRD-PARTY-NOTICES).

---

CrossMono is independent community firmware. It is not affiliated with or supported by M5Stack. PaperMono is a
product of M5Stack.
