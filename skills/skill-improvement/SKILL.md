---
name: skill-improvement
description: >
  Detects when a Claude Code session reveals a gap, bug, or improvement in an existing skill,
  then proposes a targeted patch and (with user approval) creates a local git branch and commit
  in the skills repo. Trigger this skill whenever you notice during a session that: a skill gave
  wrong or incomplete guidance, you had to correct or supplement a skill's instructions, a workaround
  was needed that should be documented, or the user says something like "the skill missed this",
  "add this to the skill", or "we should update the skill". Also trigger proactively at the end of
  any session that used a skill and produced fixes or new knowledge. Never wait for the user to ask.
---

# Skill Improvement

This skill captures knowledge gained during a working session and feeds it back into the relevant
skill — keeping skills accurate and up to date without manual maintenance.

## When to trigger

Trigger this skill whenever, during a session, you observe any of the following:

- A skill's instructions were incomplete or wrong and you had to correct course
- You discovered an edge case the skill didn't cover
- The user corrected you in a way that implies a skill gap
- A fix, workaround, or pattern emerged that should be documented for next time
- The user explicitly says "update the skill", "add this to the skill", etc.
- At **natural session wrap-up points** when a skill was actively used — proactively check if anything
  is worth capturing, even if the user didn't mention it

Don't wait to be asked. If you notice something, surface it.

## Skill repo location

The skills git repo is at: `~/Projects/claude-code-skills/`
Skills source lives at: `~/Projects/claude-code-skills/skills/`
The `~/.claude/skills/` directory contains symlinks into the above.

## The improvement flow

### Step 1 — Identify and summarize the gap

When you detect an improvement opportunity, pause and tell the user:

> "I noticed something worth capturing in the **[skill-name]** skill: [one-sentence description of the gap or fix].
> Want me to propose a patch?"

Keep it brief. Don't write the patch yet.

### Step 2 — Draft the patch

If the user says yes (or "go ahead", "sure", etc.), draft the minimal change to `SKILL.md`:

- Show a **unified diff** or clearly marked before/after block
- Keep changes surgical — fix only what was wrong, don't refactor unrelated sections
- If adding new content, place it in the most logical existing section rather than appending at the end
- If the change is substantial, briefly explain your reasoning

Then ask:

> "Does this look right, or would you like to adjust anything before I commit it?"

### Step 3 — Apply and commit (only after explicit approval)

Once the user approves (explicit "yes", "looks good", "commit it", etc.):

```bash
cd ~/Projects/claude-code-skills

# Create a branch
git checkout -b skill/<skill-name>/<short-kebab-description>

# Apply the change to the actual skill file
# (edit ~/Projects/claude-code-skills/skills/<skill-name>/SKILL.md)

# Stage and commit
git add skills/<skill-name>/SKILL.md
git commit -m "skill(<skill-name>): <short description of what was fixed/added>

Context: <one sentence about what session/task revealed this gap>"

# Report back
git log -1 --oneline
```

Branch naming convention: `skill/<skill-name>/<what-changed>`
Examples:
- `skill/zetic-melange/fix-npu-init-order`
- `skill/pdf-reading/add-scanned-doc-handling`
- `skill/skill-improvement/clarify-trigger-conditions`

Commit message format:
```
skill(<name>): <imperative short description>

Context: <what revealed the gap>
```

### Step 4 — Tell the user what to do next

After committing, tell the user:

> "Branch `skill/<name>/<desc>` is ready. Review with `git diff main skill/<name>/<desc>` in
> `~/Projects/claude-code-skills`, then merge when you're happy with it."

## What makes a good skill patch

**Do capture:**
- Missing steps that caused errors or confusion
- Edge cases that required manual correction
- Clarifications to ambiguous instructions
- New patterns or conventions that emerged from real use
- Prerequisites or environment requirements that were assumed but not stated

**Don't capture:**
- One-off project-specific details that don't generalize
- Fixes to the user's code (not the skill's instructions)
- Speculative improvements not grounded in something that actually went wrong
- Style rewrites that don't change meaning

## Multiple improvements in one session

If several gaps were found, handle them one at a time — one branch per logical change.
Don't batch unrelated fixes into one commit.

## If the affected skill is unclear

Sometimes a gap spans multiple skills or belongs in a new skill. In that case:
- If it fits mostly in one skill, put it there and note the overlap
- If it clearly belongs in a new skill, say so and offer to kick off the skill-creator flow instead
- If unsure, ask the user before proceeding

## Relation to skill-creator

This skill is about **targeted patches to existing skills based on real session observations**.
For creating a new skill from scratch, or doing a major rewrite with evals, use the `skill-creator`
skill instead. The two can hand off to each other: if a patch grows large enough to warrant
a full eval cycle, say so and suggest switching to skill-creator.
