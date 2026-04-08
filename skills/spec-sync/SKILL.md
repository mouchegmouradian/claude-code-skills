---
name: spec-sync
description: >
  Keep PRD and RFC documents in sync with code changes made during a session.
  Trigger when: user says "sync the specs/PRD/RFCs", "update the docs", "reflect these changes
  in the docs", "the PRD is stale", "docs are out of date", or after implementing an RFC.
  Also trigger when a hook reminder fires after a git commit and PRD docs exist.
  Reads git diff to understand what changed, compares against existing docs, and makes
  targeted edits — not wholesale rewrites. Never rewrite sections unaffected by code changes.
---

# Spec Sync

Keep PRD and RFC documents accurate after code changes. The goal is **surgical updates** —
only change what drifted, leave everything else intact.

## When to trigger

- User says: "sync the specs", "update the PRD", "reflect this in the RFC", "docs are stale",
  "keep the docs up to date", "update the requirements"
- After implementing an RFC (natural checkpoint)
- When a hook reminder fires after a git commit
- When requirements change mid-session and the user wants them captured

## Workflow

### Step 1 — Locate the docs

Look for a `Product requirements/` directory in the project root. Also check `docs/`,
`specs/`, `rfcs/`. If not found, ask the user where their PRD/RFC docs live.

List what you find:
- PRD file(s)
- RFC files (note their numbers and slugs)

### Step 2 — Understand what changed

First, determine the sync baseline — the commit where docs were last updated:

```bash
# Find the last commit that touched the docs directory
git log --oneline -- "Product requirements/" | head -3
```

Use that commit hash as the base. If no such commit exists (docs were never committed),
use `git log --oneline -10` and ask the user which commit to diff from.

Then gather the changes:

```bash
git diff <base>..HEAD --stat
git diff <base>..HEAD
```

Summarize in plain language:
- New files created
- Existing files modified (which areas?)
- Files deleted or renamed
- New dependencies added (package.json, pubspec.yaml, build.gradle, etc.)
- Config or schema changes

### Step 3 — Read the docs

Read every PRD and RFC file. Build a mental map:
- Scope: what's in, what's explicitly out
- Data models: field names, types, relationships
- Architecture: tech stack, patterns, service boundaries
- RFC coverage: what area each RFC owns

### Step 4 — Identify drift

Compare the code changes against the docs. Categorize each discrepancy:

| Drift type | Example |
|------------|---------|
| New feature not in docs | Added `offline_mode` flag, PRD doesn't mention it |
| Changed data model | Renamed `userId` → `accountId` in code, docs still say `userId` |
| Descoped feature | Deleted `voice_capture.dart` but RFC-003 lists it as in-scope |
| Architecture change | Switched REST → GraphQL, RFC-000 still says REST |
| New RFC needed | Added a full payments module, no RFC covers it |
| Outdated dependency | Upgraded to a major library version, tech stack table is stale |

Present the drift as a numbered list before touching anything:

```
Drift detected:
1. [PRD §4.2] Data model: `userId` is now `accountId` in code
2. [RFC-003] Voice capture is still listed as in-scope but the module was deleted
3. [PRD Features table] Missing: offline mode (added in commit abc1234)
4. [RFC-000] Architecture says REST API — code uses GraphQL since commit def5678
```

**Ask the user to confirm** before proceeding:
> "Does this match what you intended, or are any of these changes I should ignore?"

Mark which items to skip based on their answer.

### Step 5 — Propose targeted updates

For each confirmed drift item, show the exact edit as a before/after:

```
Update 1: PRD §4.2 — rename userId to accountId
  Before: "The user object contains userId (UUID), email, and displayName"
  After:  "The user object contains accountId (UUID), email, and displayName"

Update 2: RFC-003 — mark voice capture as descoped
  Before: "## Status: In scope for v1"
  After:  "## Status: Descoped — removed from MVP, may revisit in v2"
```

Do NOT propose rewrites of whole sections. Make the smallest edit that fixes the drift.

### Step 6 — Apply with approval

Ask: "Should I apply all these updates, or review them one at a time?"

Apply each change using Edit (not Write — never overwrite the whole file). After applying,
read the modified section in context to confirm it reads correctly.

### Step 7 — Update the sync log

At the bottom of the PRD, add or update a sync log:

```markdown
## Sync Log

| Date       | Commit  | Summary                                              |
|------------|---------|------------------------------------------------------|
| YYYY-MM-DD | abc1234 | Renamed userId→accountId, descoped voice capture    |
```

If the sync log section doesn't exist yet, add it at the end of the PRD.

This lets future syncs know exactly where to start (`git diff <last-sync-commit>..HEAD`).

---

## What NOT to change

- Sections unaffected by the code changes — don't "improve" them opportunistically
- RFC numbering or filenames — these are referenced across documents
- Aspirational content (future phases, v2 features) unless the code explicitly removed them
- Job stories, personas, or success metrics unless the product direction actually changed

## If a whole new RFC is needed

If the code changes represent a significant new capability with no existing RFC:

1. Tell the user: "The changes to [area] aren't covered by any existing RFC. Want me to
   draft RFC-[N+1] for it?"
2. If yes, follow Phase 4 from the `product-requirements-builder` skill
3. Update the PRD Features Overview table to include the new RFC

## Tone for drift reports

Be matter-of-fact, not alarming. Drift is normal during development — the goal is keeping
docs useful, not policing them. Frame it as: "Here's what changed, here's what the docs
say, here's the delta." Let the user decide what matters.
