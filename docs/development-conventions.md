# Development Conventions

## Purpose

These conventions apply to the Adaptive Learning Intelligence Engine codebase.

The objective is to keep the project modular, testable, readable, and maintainable as the system grows.

## General Rules

### 1. Separation of Concerns

Keep these responsibilities separate:

- presentation
- API transport
- domain logic
- persistence
- external service integration
- AI/ML logic

Do not place business logic directly inside UI components.

Do not place database access directly inside presentation components.

### 2. Strong Typing

Prefer explicit types over implicit or unvalidated structures.

All externally received data should be validated before entering domain logic.

### 3. Small Focused Modules

Prefer small modules with a clear responsibility.

Avoid creating large files that combine unrelated concerns.

### 4. Explicit Dependencies

Dependencies should be passed explicitly where practical.

Avoid hidden global state.

### 5. Deterministic Logic

Use deterministic algorithms whenever the decision itself is deterministic.

Do not make an LLM call simply to perform arithmetic, ranking, prerequisite validation, or other deterministic work.

### 6. AI Provider Isolation

External AI services must be accessed through an abstraction layer.

Domain services should not depend directly on a vendor-specific SDK.

### 7. Explainability

Important AI-assisted decisions should retain the evidence and inputs that produced the decision.

The system should be able to explain:

- why something was recommended
- why it was recommended now
- what evidence supports it
- what changed

### 8. Error Handling

Do not silently suppress errors.

Errors should either be handled explicitly or propagated to an appropriate boundary.

### 9. Configuration

Secrets and environment-specific settings must never be hardcoded into source code.

### 10. Testing

Important domain algorithms must have automated tests.

User-facing critical workflows should eventually have integration and end-to-end tests.

### 11. Documentation

Non-obvious algorithms and architectural decisions should be documented.

Documentation should be updated when architecture changes.

### 12. Dependency Discipline

Do not introduce a dependency unless it is required by the current implementation.

Prefer established, well-supported libraries over custom replacements.

## Naming

Use descriptive names.

Avoid ambiguous names such as:

```text
data
temp
helper
manager
misc