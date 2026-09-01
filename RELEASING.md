# Releasing Smart Vibe Kit

Use this checklist for a public source release. Run commands from the repository root with Python 3.11 or newer.

## 1. Confirm release metadata

- `skill/VERSION`, runtime constants, installer version, skill frontmatter, changelog, and supported-version policy agree.
- `CHANGELOG.md` describes user-visible changes.
- `skill/compatibility.json` contains a current review date and primary source for every advertised harness.
- A harness remains marked `runtime_tested: false` until a real session in that harness completes the recorded smoke workflow.

## 2. Run the gates

```text
python -B -m unittest discover -s skill/tests -v
python -B -m unittest discover -s installer/tests -v
python -B -m unittest discover -s examples/pocket-list/tests -v
python -B skill/runtime/svk.py check --package --root skill
python -B skill/runtime/svk.py check --root examples/pocket-list
python -B scripts/release_check.py
python -B scripts/verify_archive.py
```

`release_check.py` checks version consistency, required release files, Python syntax, JSON and JSONL parsing, local Markdown links, privacy leaks, cache files, the skill package, and every included example. `verify_archive.py` builds the ZIP, safely extracts it into a clean temporary directory, and runs the same release audit from the extracted tree.

## 3. Build the archive

```text
python -B scripts/build_release.py
```

This creates `dist/smart-vibe-kit-<version>.zip` and its `.sha256` file. The archive uses stable paths, timestamps, ordering, permissions, and uncompressed stored entries so identical source trees produce identical bytes across supported operating systems and zlib versions.

Run the build twice and compare hashes when changing packaging logic. Extract the archive into a clean temporary directory and run `scripts/release_check.py` from the extracted tree before publication.

## 4. Publish

1. Tag the exact reviewed source commit as `v<version>`.
2. Attach the ZIP and `.sha256` files to the release.
3. Include the compatibility qualification in the release notes: documented-but-untested harness integrations are beta.
4. Do not upgrade a host or operating-system claim from preview until its recorded runtime or CI result exists.
