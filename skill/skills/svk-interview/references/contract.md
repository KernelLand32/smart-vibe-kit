# Interview runtime contract

Call `scripts/entry.py` with the options documented in SKILL.md. The answers JSON is an object with required `title` and `idea` strings. Useful optional fields are `goals`, `non_goals`, `constraints`, `platforms`, `integrations`, `team_size`, `risk`, `research_tier`, `user_facing`, `ui`, `deployable`, `sensitive_data`, `regulated`, `include_modules`, and `exclude_modules`.

The runtime rejects unknown module names and prevents exclusions from removing risk-required modules. It stages the complete scaffold beside the target, validates it, commits only paths that do not already exist, rolls back files created by a failed commit, and validates the committed result.

Use `python scripts/entry.py --questions` to retrieve the baseline interview topics. The model should collapse questions already answered by the idea or repository evidence.
