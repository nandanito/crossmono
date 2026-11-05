## Summary

What does this change, and why? Link the issue or discussion.

## Checks

- [ ] The title is semantic (`feat:`, `fix:`, `docs:`, `chore:` …) and the branch targets `main`.
- [ ] Builds and tests pass locally (`pio run -e papermono`, `pio run -t unit-tests`, `bin/clang-format-fix`), or
      this changes documentation only.
- [ ] No CrossPoint file is deleted. Every edited CrossPoint file has its row in the seams table
      ([docs/upstream-sync.md](https://github.com/nandanito/crossmono/blob/main/docs/upstream-sync.md)).
- [ ] A changed decision has a new record or a dated addendum in
      [docs/decisions/](https://github.com/nandanito/crossmono/blob/main/docs/decisions/README.md).
- [ ] User-visible changes are in `CHANGELOG.md` under `[Unreleased]`.

## Device test

For firmware changes: what to check on the device, and on which model (PaperMono, PaperMono-Lite). A firmware pull
request is merged only after a test on a real device. Write "none" for documentation-only changes.

## Upstream

Would this help every CrossPoint device? Then it belongs in CrossPoint or the FreeInk SDK; link the upstream pull
request if this carries the change until it lands there.
