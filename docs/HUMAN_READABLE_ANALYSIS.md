# NEXUS Human-Readable Analysis

NEXUS presents analysis in five user-facing stages:

1. **Overview** — a plain-language summary of the document and the main signals that need attention.
2. **Evidence Map** — the extracted relationship graph, limited to a readable set of nodes with an inspector for details.
3. **Timeline** — meaningful events only; internal `content_posted` activity is hidden from the presentation view.
4. **Narrative** — main narrative, entities, events and locations, with technical extraction details kept collapsed.
5. **Findings** — specific review signals with confidence, source evidence and recommended changes.

## Content review signals

The content auditor can flag:

- conflicting numerical measurements;
- different explanations for an incident or outcome;
- inconsistent milestone dates;
- strong claims without an immediately visible measurement/baseline;
- repeated wording that may indicate duplicated or templated content.

These are **review signals**, not proof. In particular, NEXUS does not claim that a passage was written by AI. Writing-quality signals are presented separately from evidence findings.

## Recommended change format

Each review item is designed to answer four questions:

- **What did NEXUS notice?**
- **Why does it matter?**
- **What source evidence triggered the signal?**
- **What should the analyst check or change next?**
