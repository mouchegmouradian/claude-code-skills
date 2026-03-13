# Prompt Patterns for Coding Agents

These are lightweight prompt templates for quick, targeted tasks. For full
implementation prompts (with codebase-aware file lists, step-by-step plans,
and project conventions), use **Phase 6: Generate Implementation Prompt** in
the main skill workflow instead.

Use these patterns when you need a quick, focused prompt — for example, a
single bug fix, a test pass, or a small slice of an RFC.

## Pattern 1: Single RFC Implementation

Best for: implementing one feature area from scratch.

```
Based on RFC-[NNN]: [Feature Name]

Please implement [specific deliverable].

Files to create:
- src/[path]/[file1].[ext]
- src/[path]/[file2].[ext]
- src/[path]/[file3].[ext]

Follow [framework/language] best practices.
Use [specific library] for [specific purpose].

Do NOT implement:
- [Thing from RFC-X] (that's RFC-[X])
- [Thing from RFC-Y] (that's RFC-[Y])
```

**Why this works**: Focused scope, explicit file list, clear exclusions.

## Pattern 2: Cross-RFC Feature

Best for: features that span multiple RFCs but have a clear entry point.

```
Based on RFC-[NNN] (primary) with references to RFC-[MMM] (data models):

Implement [feature] using the data models defined in RFC-[MMM].

The [Entity] model has these fields:
- [field]: [type] — [purpose]
- [field]: [type] — [purpose]

Create:
- src/[path]/[file].[ext] — [what it does]
- src/[path]/[file].[ext] — [what it does]

The UI for this feature is in RFC-[PPP]. Do NOT implement UI — only
the [service/logic/data] layer.
```

## Pattern 3: Bug Fix / Edge Case

Best for: addressing specific edge cases documented in an RFC.

```
Based on RFC-[NNN], Section: Edge Cases, Item [N]:

The current implementation does not handle [edge case].

Expected behavior:
- When [condition], the system should [behavior]
- If [fallback condition], show [user feedback]

Affected files:
- src/[path]/[file].[ext]

Do not change any other files or features.
```

## Pattern 4: Testing

Best for: generating tests for an implemented RFC.

```
Based on RFC-[NNN], Section: Testing Strategy:

Generate tests for the [component] implementation.

Unit tests needed:
- [test case 1]
- [test case 2]
- [test case 3]

Integration tests needed:
- [flow 1]
- [flow 2]

Use [test framework]. Tests should go in:
- tests/[path]/[test_file].[ext]

The implementation is in:
- src/[path]/[file].[ext]
```

## Anti-patterns to avoid

**Too vague**: "Implement the database stuff from RFC-001."
→ Which parts? All of it? Just the schema? The sync logic?

**No exclusions**: "Build the voice recording feature."
→ Agent may also build UI, transcription, and categorization.

**Too much context**: Pasting the entire PRD + all RFCs into one prompt.
→ Agent gets confused. One RFC at a time.

**No file paths**: "Create the data models."
→ Agent guesses file names and locations, creating inconsistency.

## Tips

1. **One RFC per session** — start a new conversation for each RFC.
2. **Include data models** — even if they're from another RFC, paste the
   relevant model definitions so the agent has them.
3. **Verify before moving on** — run the code, check the tests, review
   the output before starting the next RFC.
4. **Reference the glossary** — if the agent uses wrong terminology,
   paste the glossary section and ask it to correct.
