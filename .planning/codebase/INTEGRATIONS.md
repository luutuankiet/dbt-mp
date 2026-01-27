# External Integrations

**Analysis Date:** 2026-01-27

## APIs & External Services

**CLI Tools:**
- **dbt CLI** - The application's primary function is to orchestrate and parse the output of the `dbt` command-line tool. It calls `dbt ls` and `dbt compile` using Python's `subprocess` module. This is not a network-based API integration but an integration with a local application.
  - SDK/Client: `subprocess` module
  - Auth: Not applicable

There are no network-based API integrations detected.

## Data Storage

**File Storage:**
- **Local filesystem** - The application reads a `manifest.json` file from the local disk (typically in the `target/` directory) and writes a `manifest_slim.json` file to the local disk.

## Authentication & Identity

**Auth Provider:**
- Not applicable. The tool operates on local files and does not require authentication.

## Monitoring & Observability

**Logs:**
- **Standard Output/Error** - The application uses `print()` statements to log information to `stdout` and `stderr`. No formal logging framework or external service is used.

## CI/CD & Deployment

**Hosting:**
- Not applicable. This is a command-line tool, not a hosted service.

**CI Pipeline:**
- The use of `python-semantic-release` in `pyproject.toml` strongly suggests the presence of an automated CI/CD pipeline for releases (e.g., GitHub Actions, GitLab CI), but no pipeline configuration files are present in the repository itself.

## Environment Configuration

**Required env vars:**
- None detected. Configuration is handled via CLI arguments.

**Secrets location:**
- Not applicable. The application does not handle secrets.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

---

*Integration audit: 2026-01-27*
