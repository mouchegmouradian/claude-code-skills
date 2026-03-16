# Orchestration Patterns

Reference examples for the orchestrator skill. Use these as templates when decomposing tasks into phases and writing sub-agent context briefs.

---

## Phase Breakdown Patterns

### Pattern A: Foundation → Services → UI → Shell

The most common pattern for feature-rich apps. Use when there is a clear layered dependency: project structure → data layer → business logic → UI → navigation.

```
Phase 1 — Foundation (sequential)
  1A: Project setup, folder structure, shared utilities
  1B: Data models, database schema, seeders (depends on 1A)

Phase 2 — Core Services (parallel)
  2A: Repository + use cases for domain area A
  2B: Repository + use cases for domain area B
  2C: Repository + use cases for domain area C
  [Integration: AppContainer compiles, all repositories wired]

Phase 3 — UI Features (parallel)
  3A: Shared UI components and design system
  3B: Feature A screens (ViewModels + Views)
  3C: Feature B screens (ViewModels + Views)
  3D: Feature C screens (ViewModels + Views)
  [Integration: all screens compile, no undefined component references]

Phase 4 — Navigation Shell (sequential)
  4A: App shell, tab bar, routing, settings screen
  [Final: app launches and all user flows work]
```

**When to use:** Mobile apps, desktop apps, any feature-rich client with distinct data and UI layers.

---

### Pattern B: API → Workers → Frontend

Use for backend-heavy projects or when a service layer must exist before clients can be built.

```
Phase 1 — Schema & Migrations (sequential)
  1A: Database schema, RLS policies, seed data

Phase 2 — API Layer (parallel)
  2A: Auth endpoints
  2B: Core resource endpoints
  2C: Webhook/integration endpoints
  [Integration: all endpoints return expected types, schema is consistent]

Phase 3 — Background Workers (parallel, can overlap Phase 2 partials)
  3A: Job processor A
  3B: Job processor B

Phase 4 — Frontend (parallel)
  4A: Shared components
  4B: Feature screens
  4C: Auth flows
```

**When to use:** Web apps with backend + frontend, serverless APIs, event-driven systems.

---

### Pattern C: Monolithic → Modular Split

Use when refactoring a large codebase into modules.

```
Phase 1 — Core Extraction (sequential)
  1A: Shared types, protocols, utilities extracted to Core module
  1B: Data models moved to Data module

Phase 2 — Feature Modules (parallel)
  2A: Feature A module (isolated, protocol-based interfaces)
  2B: Feature B module
  2C: Feature C module

Phase 3 — Integration (sequential)
  3A: App target updated to wire all modules
  3B: Remove old monolithic files, fix all imports
```

---

## Context Brief Patterns

### Good context brief

The example below uses an iOS/Swift project — the technology names are specific to that stack, but the **structure** (read first, deliverables as file paths, explicit exclusions, build verification) applies to any platform.

```
You are implementing [RFC-003: Category Management] for [App Name].

Tech stack: Swift 6, SwiftUI, SwiftData, @Observable ViewModels, async/await.
Architecture: Clean Architecture. UI → UseCase → Repository → SwiftData.
Naming convention: files named <Feature><Type>.swift (e.g., CategoryListView.swift).

Read these files before writing any code:
- PRD/rfc-003-categories.md — full spec for this feature
- PRD/rfc-001-data-models.md — CategoryModel schema (parent/subcategory relationships)
- PRD/rfc-000-architecture.md — folder structure, AppContainer
- Core/AppContainer.swift — add categoryRepository here

Deliverables:
- Core/Data/Repositories/CategoryRepository.swift (protocol: fetch, save, delete)
- Core/Data/Repositories/SwiftDataCategoryRepository.swift (SwiftData implementation)
- Core/Domain/UseCases/Categories/FetchCategoriesUseCase.swift
- Update Core/AppContainer.swift: add categoryRepository property, wire it

Do NOT implement: CategoryPickerView, CategoriesView, or any UI (Phase 3 handles those).
Do NOT reimplement: PersistenceController, any existing shared utilities.

Build and confirm the project compiles before reporting done.
```

**Why this works:**
- Specifies exactly which files to read before writing
- Lists deliverables as file paths, not vague capabilities
- Has explicit exclusions with reasons ("Phase 3 handles those")
- Ends with a build verification requirement

---

### Bad context brief (what to avoid)

```
Implement the categories feature. Follow the PRD and add a repository and use cases.
Make sure it works with SwiftData.
```

**Why this fails:**
- No file paths to read first → agent guesses at field names, types, relationships
- No deliverable file paths → agent creates files wherever it sees fit
- No exclusions → agent may implement UI screens that another sub-agent is also building
- No build verification → agent may report done with compilation errors

---

## Integration Checkpoint Patterns

### After Phase 1 (Foundation)

```
Verify before spawning Phase 2:
- [ ] Project builds cleanly with zero errors
- [ ] All data models are registered in PersistenceController (or equivalent)
- [ ] Folder structure matches RFC-000 exactly
- [ ] Shared utilities (formatters, extensions, constants) are in place
- [ ] AppContainer stub exists with all declared properties (even if unimplemented)
```

### After Phase 2 (Services)

```
Verify before spawning Phase 3:
- [ ] AppContainer wires all repositories and use cases (no nil/stub values)
- [ ] All repository protocols match their implementations (method signatures consistent)
- [ ] Field names in repositories match data model field names exactly
- [ ] No duplicate repository implementations
- [ ] Project builds cleanly
```

### After Phase 3 (UI)

```
Verify before spawning Phase 4:
- [ ] All shared components exist and have the expected API (no undefined references)
- [ ] ViewModels use the correct observable mechanism (@Observable, not ObservableObject)
- [ ] No two sub-agents implemented the same component independently
- [ ] All ViewModels inject dependencies from AppContainer (not direct instantiation)
- [ ] Project builds cleanly
```

---

## Conflict Resolution Patterns

### Name mismatch (most common)

**Symptom:** Sub-agent 2A created `CategoryRepository` with a method `fetchAll()`, but sub-agent 3B calls `getCategories()`.

**Fix:** Before spawning Phase 3, read every protocol defined in Phase 2 and normalize method names. Update the Phase 3 context briefs to use the correct method names.

**Prevention:** In Phase 2 context briefs, specify method names explicitly:
```
CategoryRepository protocol must define:
  func fetchAll() async throws -> [CategoryModel]
  func save(_ category: CategoryModel) async throws
  func delete(_ id: UUID) async throws
```

---

### Duplicate implementation

**Symptom:** Sub-agent 3A built a `CategoryPickerView` as a shared component; sub-agent 3D also built its own `CategoryPickerView` inline.

**Fix:** After Phase 3 completes, grep for duplicate type names. Keep the shared component version, delete the inline one, update the sub-agent's view to import and use the shared one.

**Prevention:** In Phase 3 context briefs for feature agents, explicitly list shared components they must use:
```
Use these shared components — do NOT reimplement them:
- Shared/Components/CategoryPickerView.swift (built by sub-agent 3A)
- Shared/Components/TransactionRowView.swift (built by sub-agent 3A)
```

---

### Missing dependency wiring

**Symptom:** AppContainer compiles, but a Phase 3 ViewModel crashes at runtime because a use case was never added to AppContainer.

**Fix:** After each phase, read AppContainer and cross-check against every use case and repository defined in that phase.

**Prevention:** Every Phase 2 sub-agent's context brief must include:
```
Update AppContainer.swift: add a property for [RepositoryName] and wire it using [dependency].
```
Make this a required deliverable, not a suggestion.

---

## Parallelization Decision Tree

```
Can Sub-agent B start before Sub-agent A finishes?

  Does B need to import or call any type defined in A?
  ↓ Yes → B depends on A. Run sequentially.
  ↓ No  → B is independent. Run in parallel.

  Does B write to any file that A also modifies?
  ↓ Yes → Conflict risk. Run sequentially or split the file responsibility.
  ↓ No  → Safe to parallelize.

  Does B rely on a seeded/initialized state that A creates?
  ↓ Yes → B depends on A. Run sequentially.
  ↓ No  → Safe to parallelize.
```

**Common safe parallels:**
- Multiple repositories in the same layer (each in its own file)
- UI feature screens (each in its own folder)
- Independent background workers

**Common unsafe parallels:**
- Anything that modifies AppContainer alongside another sub-agent that also modifies AppContainer → assign one sub-agent to own AppContainer updates per phase
- Data model creation + repository creation → models must exist before repositories reference them

---

## Sizing Sub-Agents

**Right-sized sub-agent:** One RFC, one feature area, 3–8 files as deliverables.

**Too large:** "Implement the entire data layer" → split into domain-specific repositories (accounts, transactions, categories, budgets each get their own sub-agent).

**Too small:** "Add one field to TransactionModel" → doesn't need orchestration at all; do it in the main agent.

**Rule of thumb:** If you can describe the sub-agent's deliverables in a 5-item bulleted list, it's well-scoped. If you need 15+ items, split it.
