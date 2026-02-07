# dbt Manifest Parser (`dbt-mp`)

*Initialized: 2026-02-07*

## What This Is

A CLI tool that intelligently slices dbt's massive `manifest.json` down to a focused, token-optimized artifact. Designed for developers and AI agents working with large dbt projects where the full manifest (300k+ tokens) is too noisy for effective analysis. Bridges the gap between `dbt ls` (too shallow) and raw manifest (too deep).

## Core Value

**Generate a hyper-focused, token-optimized slice of the dbt manifest that preserves compiled SQL and lineage context.**

The "compile first" behavior is essential — without `compiled_code`, LLMs only see Jinja templates with unresolved `{{ ref() }}` calls instead of actual SQL they can reason about.

## Success Criteria

Project succeeds when:
- [ ] Running `dbt-mp --select '+model+'` produces a valid, slimmed manifest
- [ ] Token reduction achieves ~95%+ compared to raw manifest (benchmark: 343k → <20k on jaffle_shop)
- [ ] Output includes compiled SQL, lineage graph, and essential metadata
- [ ] LLMs can effectively reason about model dependencies using the output
- [ ] Fits naturally into PR workflow (attach manifest, reviewers/LLMs can "chat with the PR")

## Context

**Technical environment:**
- Python CLI, distributed via PyPI (`pip install dbt-mp` / `uvx dbt-mp`)
- Runs from dbt project root, requires dbt CLI available
- Invokes `dbt ls` to compile and generate fresh manifest before parsing

**Prior work:**
- dbt's native manifest is comprehensive but not optimized for LLM contexts
- `dbt ls` gives model selection but no code/lineage detail
- This tool fills the gap: selected models + compiled code + lineage in one artifact

**User needs:**
- AI agents need focused context to analyze/refactor dbt models
- PR reviewers need quick way to understand change scope and dependencies
- New developers need accelerated onboarding to complex dbt projects
- Real-world usage: PR primer with manifest + static dbt docs for "chat with the PR" experience

## Constraints

- **Compile dependency:** Must run `dbt ls` first to get `compiled_code` — cannot work on stale/uncompiled manifest
- **Token budget:** Output must stay LLM-context-friendly (<50k tokens for typical selections)

## Open Questions

See INBOX.md for active exploration loops:
- LOOP-001: Optimal manifest keys for LLM context
- LOOP-002: Lineage representation strategy for context engineering

---
*Update when project scope changes (new requirements, pivot, major feature addition)*
