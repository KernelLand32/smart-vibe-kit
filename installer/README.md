# Install Smart Vibe Kit 2.0.0

The installer reads the sibling `../skill/` bundle. Keep both top-level folders together when installing from an archive or clone. Python 3.8 or newer is required; the runtime has no third-party dependencies.

## Default install

The default uses the shared Agent Skills location, which avoids duplicate copies for hosts that read `~/.agents/skills`:

```powershell
py -3 installer/install.py
```

```sh
python3 installer/install.py
```

This installs four visible skills plus one hidden shared runtime. Existing paths are replaced only when their ownership markers identify Smart Vibe Kit.

## Choose a harness

List host IDs, paths, invocation syntax, and compatibility status:

```text
python installer/install.py --list
```

Install for one host or several:

```text
python installer/install.py --target cursor
python installer/install.py --target claude,grok,qwen
python installer/install.py --target all
```

`all` avoids installing duplicate copies when several hosts use the same skill folder. For a single-host install, the installer adds that host's documented setting for preventing automatic activation when one is available. A shared install keeps the portable skill metadata because different hosts use different setting names. The main README shows how to select each action in every listed harness.

## Project-local install

```text
python installer/install.py --target agents --scope project --project-root /path/to/project
```

Use project scope when the project should carry its own skill copy. Commit it only if your team intends to share those installed artifacts.

## Preview, update, and uninstall

Preview without writes:

```text
python installer/install.py --target all --dry-run
```

Run the same install command to update an owned 2.x installation transactionally. Remove only owned SVK paths with:

```text
python installer/install.py --target agents --uninstall
```

An unowned directory with the same name is never overwritten or removed. `--dest <skill-root>` is available for custom harnesses and controlled testing.

## Launchers

On Windows, `installer/install.ps1` selects `py -3` or `python`. On macOS and Linux, `installer/install.sh` selects `python3` or `python`. Every Python option above can be passed through either launcher.

After installation, use the invocation shown by `--list`. Codex uses `$svk-interview`, `$svk-refresh`, `$svk-next`, and `$svk-check`; many slash-capable harnesses expose `/svk-interview`, `/svk-refresh`, `/svk-next`, and `/svk-check`.
