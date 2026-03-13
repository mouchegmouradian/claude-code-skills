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
- [ ] Phase 6: Generate Prompt — create implementation prompts for coding agents
```

### Output location and naming

Save all documents in a `Product requirements/` directory at the project root.
Ask the user if they prefer a different location. If a directory already exists
with PRDs or RFCs, use that location instead.

**Naming convention:**

| Document | Filename |
|----------|----------|
| PRD | `PRD-[ProjectName].md` |
| Architecture RFC | `RFC-000-architecture.md` |
| Feature RFCs | `RFC-[NNN]-[slug].md` (e.g., `RFC-003-voice-capture.md`) |

- Use zero-padded three-digit numbers: `001`, `002`, `012`
- Slugs are lowercase, hyphen-separated, 2-4 words max
- When adding RFCs to an existing project, continue the numbering sequence

### Phase 1: Discovery

Before asking questions, **read the existing codebase** if one exists. Scan the
project directory for:

- Architecture patterns (MVVM, Clean Architecture, MVC, etc.)
- Tech stack and frameworks in use
- Existing data models, schemas, and entities
- Services, APIs, and integrations already built
- Naming conventions, DI approach, project structure
- Existing PRDs or RFCs (check for a `Product requirements/`, `docs/`, `specs/`,
  or `rfcs/` directory)

This context prevents you from producing specs that conflict with the codebase.
If a PRD already exists and the user wants to add a feature, skip to Phase 3
(see "Adding an RFC to an existing project" below).

Now interview the user. Adapt your questions to what the codebase and user have
already told you — don't re-ask what's obvious from context.

**Core questions** (ask what's missing, skip what's known):

1. **What problem are you solving?** Who has this problem, and how painful is it?
2. **Who are your users?** What are their goals, frustrations, and current workarounds?
3. **What does success look like?** Measurable criteria — time saved, error rates, adoption targets.
4. **What's the MVP scope?** What's in for v1, what's explicitly out?
5. **Technical constraints?** Platform (web/mobile/both), tech stack preferences, third-party services, offline needs.
6. **What exists already?** Any prior art, mockups, codebases, or competitor references?

Capture answers in your working memory. You'll weave them into the PRD.

#### Adding an RFC to an existing project

If the project already has a PRD and the user wants to add a feature (not start
from scratch):

1. Read the existing PRD and all existing RFCs to understand current scope,
   data models, glossary, and conventions
2. Skip Phase 2 — the PRD exists
3. Go to Phase 3 to define the new RFC's scope, checking for overlap with
   existing RFCs
4. Continue with Phase 4-6 as normal
5. After drafting, update the PRD's Features Overview table with the new RFC

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

**Implementation order**: After defining all RFCs, determine the order they
should be implemented. List them with a one-line justification:

```
Implementation Order:
1. RFC-000: Architecture — foundation everything else depends on
2. RFC-001: Database & Models — data layer must exist before features
3. RFC-002: Core Feature A — primary user value, validates the architecture
4. RFC-004: API Integration — needed by Feature B
5. RFC-003: Feature B — depends on API integration
6. RFC-005: UI Polish — requires all features to be functional
```

Include this in the PRD's "Features Overview" section so the implementation
agent knows what to build first.

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

Before finalizing, **actively verify** each item — don't just eyeball it.

1. **Traceability check**: Read every JS-XXX job story in the PRD. For each one,
   search the RFC files to confirm at least one RFC references it. List any
   orphaned stories.

2. **Data model consistency**: Compare entity field names, types, and relationships
   across the PRD and every RFC that references them. Flag any mismatches
   (e.g., PRD says `categoryId: UUID` but RFC-003 says `category: String`).

3. **Scope overlap check**: For each RFC, read its "Scope Boundaries" section.
   Flag any capability that appears in more than one RFC's "This RFC covers" list.

4. **Exclusion check**: Verify each RFC has an explicit "This RFC does NOT cover"
   section with cross-references to sibling RFCs.

5. **Terminology consistency**: Pick the glossary terms from the PRD and search
   all RFC files for variant spellings or synonyms (e.g., "Note" vs "Idea",
   "Category" vs "Folder"). Fix inconsistencies.

6. **Edge case coverage**: Confirm each RFC's Edge Cases section is populated
   (not empty or placeholder). Check that error/failure scenarios are addressed,
   not just happy paths.

7. **Tech stack alignment**: Verify code samples use the language, framework,
   and libraries declared in the PRD's Technology Stack table.

8. **Performance targets**: Confirm specific numbers exist (not just "should be
   fast") with acceptable ranges.

Present the review results to the user as a checklist with pass/fail for each
item and details on anything that needs fixing.

### Phase 6: Generate Implementation Prompt

After all RFCs are reviewed and finalized, **ask the user**:

> "Would you like me to generate a complete implementation prompt for any of these RFCs? You can paste it into a new Claude Code session to implement the feature."

If the user says yes, ask which RFC(s) they want a prompt for (or offer to do all of them).

**To generate the prompt, you must:**

1. **Read the project codebase** — scan the actual project directory to identify:
   - Existing files that will be modified or replaced
   - Related services, utilities, or shared code the implementation will touch
   - Project conventions (naming patterns, DI approach, architecture style)

2. **Build the prompt** with these sections in order:

   a. **Opening context** — tell the agent what RFC to implement and where to find it (absolute path)

   b. **Files to read first** — list every existing file the agent should read before writing code:
      - The RFC document itself
      - All files that will be modified/replaced
      - Related RFCs for cross-cutting context
      - Services or utilities the implementation depends on

   c. **Step-by-step implementation plan** — ordered steps with:
      - Specific file changes (what to create, modify, rename, delete)
      - Detailed instructions for each change (not just "implement X" — spell out the logic)
      - Dependencies between steps (what must happen before what)
      - "Build after each major step to catch errors early"

   d. **Project conventions** — any patterns the agent must follow:
      - Architecture patterns (MVVM, Clean Architecture, etc.)
      - DI approach, state management, naming conventions
      - Custom colors, design tokens, shared components
      - Testing patterns, deployment targets
      - Feature flags or configuration to respect

3. **Format the prompt** as a single copyable block — the user should be able to paste it directly into a new Claude Code session with no edits needed.

**What makes a good implementation prompt:**

- **Absolute file paths** — no guessing, no relative paths from unknown roots
- **Read before write** — always tell the agent to read existing code first
- **Ordered steps** — numbered, with clear dependencies
- **Specificity over brevity** — spell out exactly what each step involves (which structs to rename, which enum cases to add, which UI sections to build)
- **Explicit exclusions** — "Do NOT touch X" or "That's handled in RFC-Y"
- **Build verification** — remind the agent to build/test after each major step
- **Plan file** — tell the agent to create a plan in `tasks/todo.md` first and mark items as it goes

See [references/example-prompt-patterns.md](references/example-prompt-patterns.md) for simpler prompt patterns that can be used as building blocks.

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
