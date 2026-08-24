# Contributing

Keep installer behavior inside `installer/` and skill behavior inside `skill/`. The installer may read the sibling skill package; the skill package must not contain installer scripts or installation procedures.

Before submitting a change:

1. Run both unit-test suites from the repository root.
2. Run `python skill/runtime/svk.py check --package --root skill`.
3. Run `python scripts/release_check.py`.
4. Run the Pocket List test suite and keep its stored SVK state unchanged.
5. Keep tests isolated in temporary directories. Tests must not modify checked-in examples or fixtures.
6. Add a negative test for every new invariant or safety boundary.
7. Update the single `skill/VERSION` source and changelog together for releases.
8. Update `skill/compatibility.json` only with dated primary documentation or a recorded runtime test for the affected host.

See [RELEASING.md](RELEASING.md) for the publish checklist and reproducible archive command.
