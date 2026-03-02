# PRD Template

Copy and adapt this template for each new product. Delete guidance comments
(lines starting with `>`) after filling in each section.

---

```markdown
# [Product Name] Product Requirements Document (PRD)

**Version:** 1.0.0
**Last Updated:** [Date]
**Status:** Draft - MVP Definition Phase

---

## Table of Contents

1. Overview
2. Problem Statement and Goals
3. User Requirements
4. Technical Requirements
5. Design Requirements
6. Success Metrics
7. Timeline and Milestones
8. PRD/RFC Approach for Development
9. Features Overview

---

## Overview

### Project Description

> One paragraph. What is this product? Who is it for? What's the core value
> proposition? Mention the primary interaction model (voice-first, web app,
> API, CLI, etc.).

### Goals and Objectives

> 1. **Primary Goal**: The single most important thing this product must do.
> 2. **Secondary Goals**: 2-4 additional objectives that support the primary goal.

### Success Criteria

> Measurable outcomes. Use specific numbers where possible:
> - "Users can [action] in under [X] seconds"
> - "[X]% accuracy for [capability]"
> - "Works offline with sync when connection restored"
> - "User satisfaction score > [X]/5.0"

---

## Problem Statement and Goals

### Problem Statement

> What pain exists today? Be specific. List 3-5 concrete failures of
> the current state. Number them — you'll reference these later.

### Business Context

> Who is the target user? Describe them in 3-4 bullet points:
> - What they do
> - How many ideas/tasks/items they deal with daily
> - What environment they work in
> - What they currently use (and why it fails)

### User Pain Points

> Direct quotes or paraphrased frustrations. Format as:
> - **"I lose ideas constantly"**: Ideas vanish in the 30 seconds it takes to...
> - **"I have hundreds of unsorted notes"**: Capturing is easy, finding later is...

---

## User Requirements

### User Personas

> For each persona (2-3 for MVP):
>
> #### [Number]. [Persona Name] (Primary/Secondary/Tertiary)
>
> - **Background**: Role, age range, context
> - **Goals**: What they want to accomplish
> - **Pain Points**: What frustrates them today
> - **Key Features Needed**: Which capabilities matter most to them
> - **Usage Pattern**: Frequency, volume, review cadence

### Job Stories

> Use the format: **When [situation], I want to [motivation], so I can [expected outcome].**
>
> Group by theme (e.g., Capture, Organization, Review). Number each story
> with a prefix (JS-001, JS-002, etc.) for traceability to RFCs.
>
> #### [Theme Name]
>
> - **JS-001**: When [situation], I want to [motivation], so I can [outcome]
> - **JS-002**: When [situation], I want to [motivation], so I can [outcome]

### Functional Requirements

> #### MVP (Version 1.0)
>
> Group by feature area. For each requirement:
> 1. State the capability
> 2. Specify behavior details
> 3. Note edge cases
> 4. Reference which job stories it satisfies
>
> #### Future (Post-MVP)
>
> List features explicitly deferred. This is as important as what's included —
> it prevents scope creep during implementation.

---

## Technical Requirements

### System Architecture

> High-level architecture description. Include:
> - Client/server split
> - Data flow diagram (ASCII art or mermaid)
> - State management approach
> - Offline strategy (if applicable)

### Technology Stack

> | Layer | Technology | Rationale |
> |-------|-----------|-----------|
> | Frontend | [framework] | [why] |
> | Backend | [service] | [why] |
> | Database | [engine] | [why] |
> | Auth | [provider] | [why] |

### API Specifications

> List key API endpoints or service interfaces. For each:
> - Method and path
> - Request/response format
> - Auth requirements
> - Rate limits

### Data Models

> Define every entity. For each:
> - Field name, type, constraints
> - Relationships to other entities
> - Indexes needed
> - Soft delete strategy (if applicable)
>
> Use a consistent format. Example:
>
> ### [Entity Name] Model
>
> **Purpose**: [one sentence]
>
> **Fields**:
> - `id`: UUID (primary key)
> - `name`: String (required, unique per user)
> - `createdAt`: Timestamp
> - `updatedAt`: Timestamp
> - `deletedAt`: Timestamp? (soft delete)

### Security Considerations

> - Authentication method
> - Data encryption (at rest, in transit)
> - Permission model (RLS, RBAC, etc.)
> - Privacy considerations (what data stays on-device, what goes to cloud)

### Performance Requirements

> | Operation | Target | Acceptable Max |
> |-----------|--------|----------------|
> | [action] | <Xms | Xms |

---

## Design Requirements

> Interaction patterns, accessibility requirements, platform-specific
> considerations. Include ASCII wireframes for key screens if helpful.

---

## Success Metrics

> Quantitative measures tied directly to the goals from the Overview section.
> Each metric should be measurable and have a target value.

---

## Timeline and Milestones

> Break into 2-week phases. For each phase:
> - What gets built
> - What gets tested
> - Key deliverables

---

## PRD/RFC Approach for Development

> Explain the PRD → RFC → Implementation workflow.
> List all planned RFCs with their scope.
> Include the recommended prompt pattern for feeding RFCs to coding agents.

---

## Features Overview

> Summary table linking each feature to its RFC:
>
> | Feature | Status | RFC | Summary |
> |---------|--------|-----|---------|
> | Architecture | ✅ Complete | RFC-000 | ... |
> | Database | 📝 Planned | RFC-001 | ... |

---

## Appendix

### Glossary

> Define every domain-specific term. This is critical — inconsistent
> terminology causes coding agents to create duplicate concepts.

### References

> Links to frameworks, libraries, APIs, design systems referenced in this PRD.

### Document History

> | Version | Date | Author | Changes |
> |---------|------|--------|---------|
> | 1.0.0 | [date] | [author] | Initial PRD |
```
