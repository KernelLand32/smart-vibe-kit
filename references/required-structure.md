# Required project structure (bootstrap output)

When `/smart-vibe-kit <idea>` runs, the agent **must create every path below** in the **current workspace** before handing off. Partial scaffolds are a failure.

Populate with **idea-specific content** (rewrite templates — no `{placeholders}` left outside `docs/_templates/`).

**Canonical checklist** — `SKILL.md` and adapters link here; do not duplicate the tree elsewhere.

## Mandatory tree

```text
AGENTS.md
docs/
  constitution.md
  registry.md
  tasks.md
  documentation-strategy.md
  verification-gates.md
  toolchain-pins.md
  roadmap.md
  research/
    profile.md
    landscape.md               # findings OR explicit skipped note with reasons
  adr/
    _template.md
    0001-project-charter.md    # status: accepted (bootstrap) or proposed→user accept
    0002-authorize-phase1-stage1.md  # accepted on bootstrap invoke
  _templates/
    deliverable-spec.md
    phase-archive.md
  checklists/
    done.md
    stage-gate.md
    pr.md
  workflows/
    README.md
    constitute.md
    specify.md
    authorize.md
    plan-tasks.md
    implement.md
    verify.md
    close-stage.md
    recover.md
    refresh.md
  archives/                    # may be empty except .gitkeep or README
    README.md
  {area1}/                     # ≥2 domain areas inferred from the idea
    …                          # ≥1 deliverable with claims / OQ / gates
  {area2}/
    …
scripts/
  verify_structure.py          # copy from skill scripts/verify_structure.py
```

### Domain areas

Infer **at least two** `docs/{area}/` folders from the idea (e.g. `product` + `engineering`).  
Each area must contain **at least one** deliverable with:

- Verifiable claims table  
- Real sections (not empty headings)  
- Open questions `OQ-…`  
- Gate checklist  

Process directories (`adr`, `research`, `_templates`, `checklists`, `workflows`, `archives`, `dev`, `plan`) do **not** count as domain areas.

### Archives

Closed phases → `docs/archives/phase-N-slug.md` (see phase-archive template).  
`docs/archives/README.md` can state “no closed phases yet.”

## Source of templates

Copy-from-then-rewrite under the **installed skill package**:

`~/.cursor/skills/smart-vibe-kit/assets/templates/`  
(Windows: `%USERPROFILE%\.cursor\skills\smart-vibe-kit\assets\templates\`)

Workflows/checklists: copy from skill `references/workflows/` and `references/checklists/` into `docs/workflows/` and `docs/checklists/` (adjust relative links to project paths).

Also follow skill: `SKILL.md`, `references/research-gate.md`, `references/bootstrap.md`, `references/constitution.md`.

## Done criteria

1. Every mandatory path exists  
2. `docs/tasks.md` has a single **Next action**  
3. Every task ID appears in `docs/registry.md`  
4. No unresolved `{brace}` placeholders outside `docs/_templates/`  
5. `python scripts/verify_structure.py --root . --bootstrap` exits 0  

```bash
python scripts/verify_structure.py --root . --bootstrap
```
