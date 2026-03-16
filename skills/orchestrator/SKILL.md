---
name: orchestrator
description: Coordinate large, multi-feature implementations by acting as an orchestrator that spawns focused sub-agents — one per RFC or feature area — while managing phasing, parallelization, and integration verification. Use this skill when a task spans 3+ independent features, multiple RFCs, or requires parallel implementation across different areas of the codebase. Also triggers on phrases like "orchestrate this", "spawn sub-agents", "implement all RFCs", "parallel implementation", "multi-agent", or "build the full app". Do NOT use for single-feature or single-file tasks — those should be implemented directly.
---

# Orchestrator

Coordinate large implementations by acting as a planning-and-verification layer. Your job is to define phases, spawn focused sub-agents, and integrate their output — not to write code yourself.

**This skill is the execution half of a two-skill pipeline:**
1. `product-requirements-builder` — produces the PRD and RFCs (the *what* and *how*)
2. `orchestrator` (this skill) — executes them by coordinating sub-agents (the *doing*)

If no PRD/RFCs exist yet, use `product-requirements-builder` first. The orchestrator works best when it has a PRD and a set of RFCs to work from — they define the scope boundaries that prevent sub-agents from drifting.

## Complexity Gate — Choose Your Mode

Before anything else, assess the task:

```
Is this task...

  Single file or focused area?
  ↓ Yes → Implement directly. This skill is not needed.

  2–5 files, one feature, sequential steps?
  ↓ Yes → Plan in tasks/todo.md, implement in main agent.

  3+ independent features, multi-RFC, or parallel work?
  ↓ Yes → Use this skill. Continue below.
```

**Signals that warrant orchestration:**
- Implementation spans 3+ RFCs or feature areas
- Features can be built in parallel (no shared dependencies within a phase)
- Task is large enough that holding all context in one agent would degrade quality
- A product requirements document (PRD) or implementation prompt already exists

**Signals that do NOT warrant orchestration:**
- Bug fix, refactor, or single-screen addition
- Adding a new field or updating an existing component
- Task the user described in 1–2 sentences with no phase structure

---

## Your Role as Orchestrator

You **plan, coordinate, and verify**. You do not write implementation code.

Your outputs are:
1. An **orchestration plan** — phases, sub-agents, dependencies, parallelization
2. **Context briefs** — the task description passed to each sub-agent
3. **Integration reviews** — verification after each phase before proceeding
4. A **final verification checklist** — end-to-end correctness check

---

## Step 1 — Read First

Before defining any phases or spawning sub-agents, read:

- The **PRD** — produced by `product-requirements-builder`, typically at `PRD/PRD-[ProjectName].md` or `Product requirements/PRD-[ProjectName].md`
- The **architecture RFC** (`RFC-000`) — project structure, conventions, DI approach, naming rules
- The **data models RFC** (`RFC-001`) — entity names, field types, relationships, constraints
- Any other RFCs in scope — read them all before defining your phase breakdown

If no PRD or RFCs exist, stop and use the `product-requirements-builder` skill first. Orchestrating without clear scope boundaries causes sub-agents to drift and conflict.

This prevents sub-agents from producing conflicting code. Understanding the data model and naming conventions is critical — inconsistencies here cascade across the entire implementation.

---

## Step 2 — Define Phases

Decompose the implementation into phases where:
- **Each phase** contains work that can begin only after the previous phase completes
- **Within a phase**, sub-agents that have no dependencies on each other run in parallel
- **Each sub-agent** has a single, well-bounded scope (one RFC, one feature area)

**Common phase structure:**

```
Phase 1 — Foundation (sequential)
  1A: Project setup / scaffolding
  1B: Data models (after 1A)

Phase 2 — Core Services (parallel, after Phase 1)
  2A: Repository + use cases for Feature A
  2B: Repository + use cases for Feature B
  2C: Repository + use cases for Feature C
  [Integration checkpoint before Phase 3]

Phase 3 — UI Features (parallel, after Phase 2)
  3A: Shared UI components
  3B: Feature A screens
  3C: Feature B screens
  [Integration checkpoint before Phase 4]

Phase 4 — Navigation & Integration (after Phase 3)
  4A: App shell, tab bar, routing, settings
```

Adjust to the project. A smaller project might only need 2 phases. The key invariant: **every sub-agent in a phase can start without waiting for siblings**.

---

## Step 3 — Write the Orchestration Plan

Before spawning any sub-agents, write your plan to `tasks/todo.md`:

```markdown
# Orchestration Plan — [Project Name]

## Phase 1 — Foundation
- [ ] 1A: [scope] — depends on: nothing
- [ ] 1B: [scope] — depends on: 1A

## Phase 2 — [Name] (parallel)
- [ ] 2A: [scope]
- [ ] 2B: [scope]
- [ ] Integration checkpoint

## Phase 3 — [Name] (parallel)
- [ ] 3A: [scope]
- [ ] ...
- [ ] Integration checkpoint

## Phase 4 — [Name]
- [ ] 4A: [scope]

## Final Verification
- [ ] End-to-end checklist
```

Mark items complete as phases finish.

---

## Step 4 — Spawn Sub-Agents

For each sub-agent, construct a context brief using this template:

```
You are implementing [feature/RFC name] for [project name].

Project context:
- [Tech stack, one line]
- [Key conventions: naming, DI, money/ID rules, etc.]
- [Critical shared components this agent must use but not reimplement]

Read these files before writing any code:
- [RFC document path]
- [Related files to understand before modifying]
- [Shared components or utilities this feature depends on]

Your task:
[Specific deliverables — file paths, what each file must contain]
[Explicit scope: "Do NOT implement X — that is handled elsewhere"]

Build and verify your work compiles before reporting back.
```

See [references/orchestration-patterns.md](references/orchestration-patterns.md) for full examples.

**Within a phase:** spawn all parallel sub-agents in a single message (one Agent tool call per sub-agent, sent simultaneously).

**Between phases:** wait for all sub-agents in the current phase to complete and pass integration review before spawning the next phase.

---

## Step 5 — Integration Review (between phases)

After each phase completes, verify before proceeding:

**Code consistency checks:**
- Entity/model names match across all sub-agents (field names, types, relationships)
- No `nil`/stub values remain in the dependency injection container
- No duplicate implementations of the same utility or component
- Import paths and module references are correct

**Architectural checks:**
- All sub-agents followed the naming conventions from RFC-000
- Money/currency types are correct (e.g., `Int64` cents, not `Double`)
- Shared components are being used, not reimplemented

**Build check:**
- The project should compile cleanly at the end of each phase before the next begins

If any sub-agent produced conflicting or incomplete output, fix it before moving forward. Do not accumulate drift across phases.

---

## Step 6 — Final Verification Checklist

After all phases complete, verify end-to-end:

- App/service launches without errors
- Primary user flows work as intended
- No stub or unimplemented code remains
- All integration points wired correctly (DI container, routing, event handlers)
- Edge cases from the PRD are covered
- Build passes cleanly

---

## What to Tell Each Sub-Agent (Full Example)

```
You are implementing the Accounts feature (RFC-013) for [App Name].

Tech stack: Swift 6, SwiftUI, SwiftData, async/await, @Observable ViewModels.
Money rule: all amounts as Int64 cents, never Double.
UUID rule: all IDs are UUID, generated client-side.
Architecture: Clean Architecture — UI → Domain (Use Cases) → Data (Repositories).

Read these files before writing any code:
- PRD/rfc-013-accounts.md
- PRD/rfc-001-data-models.md (for AccountModel schema)
- PRD/rfc-000-architecture.md (for AppContainer, folder structure)
- Core/AppContainer.swift (you will add account dependencies here)

Your deliverables (all file paths relative to project root):
- Core/Data/Repositories/AccountRepository.swift (protocol)
- Core/Data/Repositories/SwiftDataAccountRepository.swift (implementation)
- Core/Domain/UseCases/Accounts/SaveAccountUseCase.swift
- Core/Domain/UseCases/Accounts/FetchAccountsUseCase.swift
- Update Core/AppContainer.swift to wire accountRepository and account use cases

Do NOT implement: account UI screens (that is a separate sub-agent).
Do NOT reimplement: PersistenceController or any existing shared utilities.

Build and confirm the project compiles before reporting back.
```

---

## Reference

- [references/orchestration-patterns.md](references/orchestration-patterns.md) — Phase breakdown examples, context brief patterns, integration checkpoint patterns, conflict resolution
- See `example-implementation-prompt.md` at the project root for a complete real-world orchestration prompt (Kasa iOS app, 4 phases, 12 sub-agents)
