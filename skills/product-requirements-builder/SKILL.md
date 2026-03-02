---
name: product-requirements-builder
description: Build comprehensive product requirements documents (PRDs) and technical RFC specifications for software projects. Guides the user through structured discovery — from problem statement and user personas to technical architecture, data models, and implementation RFCs. Use this skill whenever the user wants to plan a new product, define requirements for a feature, create technical specs, write an RFC, break down a project into implementable pieces, or prepare documentation for AI-assisted coding (Claude Code, Cursor, etc.). Also use when the user says things like "help me spec this out", "let's plan this project", "write a PRD", "create an RFC", "break this into tasks", or "I need to define requirements for...".
---

# Building Product Requirements

Help users create professional, implementation-ready product requirements. The
output is a PRD (the "what" and "why") plus a set of focused RFCs (the "how"),
designed so that a coding agent can pick up any single RFC and implement it
with minimal hallucination.

## Why this structure matters

A PRD without RFCs is too vague for implementation. RFCs without a PRD lack
product context and user grounding. The combination gives coding agents:

- **Focused context** — each RFC addresses one implementation area
- **Clear boundaries** — explicit scope prevents agents from drifting
- **Traceability** — every technical decision links back to a user need
- **Reduced errors** — smaller, well-defined documents produce better code

## Workflow overview

Copy this checklist and track progress:

```
Requirements Progress:
- [ ] Phase 1: Discovery — understand the product vision
- [ ] Phase 2: PRD Draft — write the product requirements document
- [ ] Phase 3: RFC Breakdown — identify implementation areas
- [ ] Phase 4: RFC Drafting — write each RFC
- [ ] Phase 5: Review — validate completeness and consistency
```

### Phase 1: Discovery

Interview the user to understand their product. Don't skip this — even a brief
conversation dramatically improves the output. Adapt your questions to what the
user has already shared; don't re-ask what's obvious from context.

**Core questions** (ask what's missing, skip what's known):

1. **What problem are you solving?** Who has this problem, and how painful is it?
2. **Who are your users?** What are their goals, frustrations, and current workarounds?
3. **What does success look like?** Measurable criteria — time saved, error rates, adoption targets.
4. **What's the MVP scope?** What's in for v1, what's explicitly out?
5. **Technical constraints?** Platform (web/mobile/both), tech stack preferences, third-party services, offline needs.
6. **What exists already?** Any prior art, mockups, codebases, or competitor references?

Capture answers in your working memory. You'll weave them into the PRD.

### Phase 2: PRD Draft

Use the PRD template. See [templates/prd-template.md](templates/prd-template.md)
for the full template with section guidance.

**Key sections** (every PRD needs these):

1. **Overview** — project description, goals/objectives, success criteria
2. **Problem Statement** — the pain, the business context, user pain points
3. **User Requirements** — personas, job stories (not user stories), functional requirements broken into MVP vs. future
4. **Technical Requirements** — architecture overview, tech stack, API specs, data models, security, performance targets
5. **Design Requirements** — interaction patterns, accessibility, platform-specific considerations
6. **Success Metrics** — quantitative measures tied to goals
7. **Timeline** — milestones and phases
8. **Features Overview** — summary table linking each feature to its RFC
9. **Glossary** — define every domain term; this prevents agent confusion

**Writing principles:**

- Use **job stories** ("When [situation], I want to [motivation], so I can [outcome]") rather than user stories. They focus on context and motivation rather than role.
- Be specific about **what's in scope and what's not**. Ambiguity is where coding agents hallucinate.
- Include **edge cases** in functional requirements. If you can think of it, write it down.
- Define **data models early** — field names, types, relationships, constraints. These are the foundation everything else builds on.

### Phase 3: RFC Breakdown

Decompose the product into discrete, implementable RFCs. Each RFC should:

- Be implementable independently (or with explicit dependencies noted)
- Have clear inputs and outputs
- Map to a logical area of the codebase
- Be small enough that a coding agent can hold the full context

**Common decomposition pattern:**

| RFC | Area | Typical Content |
|-----|------|----------------|
| RFC-000 | Architecture Overview | User flows, state management, service architecture, performance targets |
| RFC-001 | Database & Data Models | Schema, ORM models, migrations, sync strategy, RLS policies |
| RFC-002 | Core Feature A | The primary user-facing capability |
| RFC-003 | Core Feature B | Secondary capability |
| RFC-004 | Integration / API | External service integration, edge functions |
| RFC-005 | UI Components | Screens, navigation, state management, accessibility |

Adapt this to the project. A simple web app might need 3 RFCs. A cross-platform
mobile app might need 6+. Always start with RFC-000 as the architecture overview
that all other RFCs reference.

### Phase 4: RFC Drafting

Use the RFC template. See [templates/rfc-template.md](templates/rfc-template.md)
for the full template with section guidance.

**Each RFC must include:**

1. **Overview** — what this RFC covers, one paragraph
2. **Goals** — numbered list, specific and testable
3. **Technical Design** — architecture, data flow, code structure
4. **Implementation Details** — platform-specific code samples, file paths, configuration
5. **Edge Cases** — every failure mode you can anticipate, with handling strategy
6. **Testing Strategy** — unit tests, integration tests, manual testing checklist
7. **Security Considerations** — auth, data privacy, permissions
8. **Dependencies** — libraries, APIs, other RFCs this depends on
9. **Related Documents** — links back to PRD and sibling RFCs

**Writing principles for RFCs:**

- Include **code samples** in the language/framework of the project. Not pseudocode — actual compilable/runnable snippets.
- Specify **file paths** where code should live (e.g., `src/database/schema.ts`).
- List **explicit exclusions** — "Do NOT implement X (that's RFC-003)". This prevents coding agents from scope-creeping.
- Use **consistent naming** across all RFCs. If the PRD calls it "Idea", every RFC calls it "Idea" (not "Note" or "Entry").

### Phase 5: Review

Before finalizing, validate:

- [ ] Every job story in the PRD maps to at least one RFC
- [ ] Every data model field is consistent across PRD and all RFCs
- [ ] No two RFCs overlap in scope
- [ ] Each RFC has explicit "do not implement" boundaries
- [ ] Glossary terms are used consistently everywhere
- [ ] Edge cases are documented (not deferred)
- [ ] Code samples match the declared tech stack
- [ ] Performance targets are stated with acceptable ranges

## Prompt patterns for coding agents

After the PRD and RFCs are complete, the user can feed individual RFCs to a
coding agent. Recommend this pattern:

```
Based on RFC-001: Database Schema & Sync

Please implement the database schema and TypeScript interfaces.

Files to create:
- src/database/schema.ts
- src/models/Idea.ts
- src/models/Category.ts
- src/database/migrations/001_initial.sql

Follow [framework] best practices.

Do NOT implement:
- API sync logic (that's RFC-006)
- UI components (that's RFC-005)
```

This pattern gives the agent focused context, clear deliverables, and explicit
boundaries.

## Adapting to project scale

**Small project** (landing page, simple tool, single-platform app):
- Combine PRD into a shorter format — skip personas if there's only one user type
- 2-3 RFCs may be sufficient
- Architecture overview can be a section within the PRD rather than a separate RFC

**Medium project** (multi-feature app, API + frontend):
- Full PRD with all sections
- 4-6 RFCs
- Separate architecture RFC (RFC-000)

**Large project** (cross-platform, multiple integrations, team of developers):
- Full PRD, possibly with appendices
- 6+ RFCs, potentially with sub-RFCs for complex areas
- Consider a "RFC-000: Architecture" that serves as the index document
- Add a dependency graph showing RFC implementation order

## Reference files

- [templates/prd-template.md](templates/prd-template.md) — Full PRD template with section-by-section guidance
- [templates/rfc-template.md](templates/rfc-template.md) — Full RFC template with section-by-section guidance
- [references/job-stories-guide.md](references/job-stories-guide.md) — How to write effective job stories
- [references/example-prompt-patterns.md](references/example-prompt-patterns.md) — Prompt patterns for feeding RFCs to coding agents
