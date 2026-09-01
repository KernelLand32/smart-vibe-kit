# Verification strategy

Project: **Pocket List**

## Required gates

1. Structure: all profile-required artifacts exist and contain substantive text.
2. State: task IDs, dependencies, status, and `next_action` agree.
3. Evidence: every required verifier has a fresh SVK-created receipt bound to the task inputs.
4. References: relative Markdown links resolve inside the project.
5. Safety: no incomplete transaction or live lock remains.

## Evidence format

SVK stores immutable verifier receipts under `.svk/evidence/runs/` and indexes them in `.svk/evidence/index.json`. Human notes and cooperative attestations may add context but do not replace a required verifier receipt.

## Release gate

The project is release-ready only when the SVK Check result is `PASS` and the release task has fresh passing receipts for every configured release verifier.
