## Summary

<!-- What changed and why -->

## Test plan

- [ ] `python scripts/verify_skill_package.py`
- [ ] `python -m unittest discover -s tests -v`
- [ ] If installable files changed: updated `scripts/install-manifest.txt`
- [ ] If bootstrap/tree rules changed: regenerated example still passes `--bootstrap --strict`
- [ ] No personal/machine-specific paths introduced (privacy scan clean)

## Notes

<!-- Breaking changes, follow-ups, screenshots -->
