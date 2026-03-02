# RFC Template

Copy and adapt this template for each RFC. Delete guidance comments
(lines starting with `>`) after filling in each section.

---

```markdown
# RFC-[NNN]: [Feature Name]

**Status**: 📝 Draft
**Created**: [Date]
**Last Updated**: [Date]

---

## Overview

> One paragraph. What does this RFC cover? What part of the system does it
> define? Reference the PRD and any prerequisite RFCs.

## Goals

> Numbered list of specific, testable goals. Each goal should be verifiable
> after implementation. Example:
>
> 1. Define data models that work on [platform A] and [platform B]
> 2. Implement [specific capability] with [specific performance target]
> 3. Handle [edge case] gracefully with [fallback strategy]

## Technical Design

### Architecture

> How this component fits into the overall system. Include:
> - Data flow diagram (ASCII or mermaid)
> - Component relationships
> - Integration points with other RFCs

### [Component/Subsystem Name]

> For each major component in this RFC:
>
> **Purpose**: What it does
>
> **Interface**: Public API, props, methods
>
> **Behavior**: How it works, state transitions, data transformations

## Implementation Details

### [Platform A] Implementation

> Platform-specific code samples. Use the actual language and framework.
> Include file paths where code should live.
>
> ```[language]
> // src/[path]/[filename].[ext]
> [actual code sample]
> ```

### [Platform B] Implementation (if cross-platform)

> Same structure, different platform.

### Configuration

> Environment variables, feature flags, default values.
> Include example configuration files.

## Edge Cases

> Number each edge case. For each:
>
> 1. **[Edge case name]**
>    - Trigger: What causes this condition
>    - Impact: What goes wrong if unhandled
>    - Handling: Specific strategy (retry, fallback, user prompt, etc.)
>    - Code: Brief code sample if the handling is non-obvious

## Testing Strategy

### Unit Tests

> What to unit test. List specific test cases, not just areas.
> Example:
> - Category parser with "This is for Work" → categoryId matches "Work"
> - Category parser with no category mentioned → categoryId is null

### Integration Tests

> End-to-end flows to test. Example:
> - Full capture flow: widget → record → transcribe → save
> - Error recovery: permission denial → text input fallback

### Manual Testing Checklist

> - [ ] [Specific observable behavior]
> - [ ] [Specific observable behavior]
> - [ ] [Specific observable behavior]

## Security Considerations

> Security relevant to this specific RFC. Reference the PRD's security
> section for system-wide concerns. Cover:
> - Data privacy (what stays on device, what goes to cloud)
> - Authentication/authorization for this component
> - Input validation and sanitization

## Dependencies

> **Libraries/Packages**:
> - `package-name` — what it's used for
>
> **Other RFCs**:
> - RFC-000: Architecture (references state management approach)
> - RFC-001: Database (provides data models used here)
>
> **External Services**:
> - [Service name]: [what it provides], [cost implications]

## Scope Boundaries

> **This RFC covers:**
> - [specific thing]
> - [specific thing]
>
> **This RFC does NOT cover (see other RFCs):**
> - [thing] → RFC-[NNN]
> - [thing] → RFC-[NNN]
>
> These exclusions are critical. They prevent coding agents from
> implementing features that belong in other RFCs.

---

## Related Documents

- [PRD: Product Name](../PRD-ProductName.md)
- [RFC-000: Architecture](./RFC-000-architecture.md)
- [RFC-NNN: Related Feature](./RFC-NNN-feature.md)
```
