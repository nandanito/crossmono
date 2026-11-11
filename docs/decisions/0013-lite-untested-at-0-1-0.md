# 0013. The Lite at 0.1.0: untested, reports welcome

- Status: Accepted
- Date: 2026-11-07

## Context

[ADR 0003](0003-two-models.md) and [ADR 0012](0012-boot-model-probe.md) say that a community tester with a
PaperMono-Lite must confirm the Lite path before `0.1.0` stable. Nobody has done that yet. Nandan has no Lite, and
on 2026-11-07 M5Stack's shop lists it as on backorder. Waiting for a tester would hold `0.1.0` for an unknown
time.

What is known without a Lite:

- Both models have the same board apart from the NFC board, the LoRa module and the LoRa load switch, which the
  Lite does not have (0003, and the V0.6.2 schematics cited in 0012). The pins that the model probe drives end at
  open nets on the Lite (0012).
- The model probe uses the same check as M5Stack's own firmware, which serves both models from one image (0012).
  When no NFC chip answers, or the IO expander cannot be written, the result is PaperMono-Lite.
- M5Stack links the same CrossPoint image for both models (0003).
- On the full model, the Model setting can be set to PaperMono-Lite, and that path works (device test of
  PR #10, 2026-11-04). This does not test the Lite hardware itself.

## Options

1. **Wait for a Lite tester before `0.1.0`.** This follows 0003 and 0012, but it holds the release for an unknown
   time, and full-model users wait too.
2. **Release `0.1.0` with the Lite marked as untested, and ask for reports after the release.** Lite owners can
   still install it, knowing the risk, and a report can lead to a `0.1.x` fix.
3. **Leave the Lite out of `0.1.0`.** The image would be the same, so this only hides it from the people who could
   test it.

## Decision

Option 2.

- `0.1.0` is released after the hardware checklist passes on the full model. The Lite does not have to be tested
  first.
- The release notes, the README, `docs/install.md` and the install page say plainly that the Lite has not been
  tested, and ask Lite owners for a report in an issue.
- The `0.1.0` announcement asks for a Lite tester ([0011](0011-community-launch.md)).
- Later releases follow the same rule until someone has tested a Lite: the checklist's Lite items are run when a
  Lite is available; otherwise the release record says "Lite: untested".

This replaces the line "A community tester with a Lite must confirm the Lite path before `0.1.0` stable" in 0003
(Decision) and 0012 (Consequences). The rest of both records stands.

## Consequences

- A Lite owner takes a known risk. The install docs tell them how to save a backup of the whole flash first and how
  to write it back.
- The first Lite report, good or bad, goes into the README and `docs/install.md`. If the Lite does not boot or
  misbehaves, the README, `docs/install.md` and the install page warn Lite owners until a fix is released.
- [docs/hardware-test-checklist.md](../hardware-test-checklist.md) keeps its Lite items.

## Addendum 2026-11-07: no 0.1.0 announcement

`0.1.0` was released on 2026-11-07 without an announcement (Nandan, 2026-11-07). The first announcement comes with
`0.2.0` ([0014](0014-cues-and-keys.md)), so the request for a Lite tester in the Decision moves to the `0.2.0`
announcement. The rest of the decision stands: `0.2.0` is released after the checklist passes on the full model,
and its release record says "Lite: untested" unless a Lite owner has reported.
