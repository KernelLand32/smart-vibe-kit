# Research gate

Decide whether `/smart-vibe-kit` must ground the idea in **current external information** before writing product claims.

## Decision rubric

Score the project idea. Research is **recommended** if **any** apply; **required** if two or more **strong** signals apply.

| Signal | Strength | Examples |
|--------|----------|----------|
| Unfamiliar / niche domain | Strong | Regulated industries, specialized hardware, rare protocols |
| Fast-moving tech | Strong | LLM APIs, mobile OS capabilities, cloud product SKUs, JS frameworks |
| Competitive / market claims | Strong | “Better than X”, pricing, feature parity tables |
| Legal / safety / medical / finance | Strong | Compliance regimes, clinical claims |
| Vendor- or standard-specific APIs | Medium | Exact endpoint names, SDK versions, rate limits |
| Well-known evergreen pattern | Weak / skip | Todo list, static blog, CRUD with boring stack |
| User already pasted authoritative sources | Skip external | Treat pasted docs as P0; still cite them |

## Hard stops

1. When research is **required** (two or more strong signals): you **must** run live web research (or use user-pasted P0 sources). Do **not** treat “ask permission once” as a skip. If the user explicitly forbids network research, continue only with `[ASSUMPTION: no live research]` on every load-bearing claim **and** put the **non-reliance banner** in ADR-0001 (see charter template).  
2. When research is **recommended** (one strong or several medium): announce reasons + topics; run research by default; a single user “skip” is allowed → labeled assumptions + landscape “skipped” note.  
3. When **weak / skip**: write landscape explaining why; no fake competitor matrices.

## Quality bar (when research runs)

- Prefer primary sources: official docs, standards, RFCs, regulator pages, measurable product pages.  
- Limit **3–7** topics.  
- Every load-bearing sentence: claim tag or Verifiable claims row with **URL + access date**.  
- Minimum **two** independent P0/P1 sources for any competitive or compliance claim.  
- Marketing blogs alone do **not** satisfy competitive/compliance claims.  
- Unknowns stay `[OPEN QUESTION]` / `[DECISION NEEDED]`.

## How to run research

1. Announce: “Research gate: {reasons}. Topics: …”  
2. Use web search / fetch tools when available.  
3. Write topic notes into `docs/research/landscape.md` (and optional `docs/research/{topic}.md`).  
4. Always write `docs/research/profile.md`.  

### If tools cannot reach the network

Ask the user to either:

- paste source links / notes, or  
- approve continuing with **explicitly labeled assumptions** and a task to re-run research later  

For medical / legal / finance / safety: also require the charter non-reliance banner. Do not silently pretend research happened.

## Output that bootstrap must consume

- `docs/adr/0001-project-charter.md` (context citations)  
- Domain deliverable specs (only claims you can source)  
- `docs/tasks.md` exploration tasks that close remaining OQs  

## Anti-patterns

- Inventing competitor feature matrices from memory  
- Pinning library versions without checking current docs  
- Skipping **required** research because “we can always fix specs later”  
- Filling gaps with plausible defaults  
