# recover

Respond to hallucination or a wrong guess without silent rewrite.

## Steps

1. State what was claimed and why it was wrong.  
2. Cite the correct P0–P2 source (or measure it now).  
3. Patch the authoritative deliverable spec.  
4. Add or supersede an **ADR** if the mistake was a decision/ambiguity.  
5. Add a registry **decision audit** row if agents will hit this again.  
6. Add a test or structural check when the failure mode is repeatable.  
7. If work was marked `done` on false evidence, revert status to `in_progress`.  

## Done when

- The wrong claim cannot be “rediscovered” as truth from docs alone  
- Evidence trail exists for the correction  
