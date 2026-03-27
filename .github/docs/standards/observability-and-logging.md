# Observability & Logging Standards

> **Requirement**: Structured logging is a permanent, first-class feature — not temporary scaffolding. Every project must implement leveled logging, automatic log file capture, and a standard artifact location so UAT teams can reference logs directly when submitting reports.

---

## Log Levels

Use four levels, mapped to integer severity values:

| Level | Value | When to use |
|-------|-------|-------------|
| `error` | 0 | Unrecoverable failures, exceptions, data loss conditions |
| `info`  | 1 | Normal operation milestones (start, completion, key state changes) |
| `debug` | 2 | Diagnostic detail useful during development and investigation (inputs, outputs, branching decisions) |
| `trace` | 3 | Deep visibility — full payloads, stack frames, inter-service calls, timing at every step |

**Level semantics**: a configured level of `N` emits all messages at severity ≤ N.
- `verbose=0` → errors only
- `verbose=2` → errors + info + debug
- `verbose=3` → full trace output (root cause analysis)

---

## Configuration Parameters

Every project must support both a CLI flag and an environment variable. The CLI flag takes precedence over the env var.

### CLI flags

```
--verbose {0,1,2,3}   Sets overall log verbosity (default: 1)
--debug   {0,1,2,3}   Sets debug detail level; implies --verbose 2 at minimum (default: 0)
```

### Environment variables

```
VERBOSE=<0-3>
DEBUG=<0-3>
```

**Example (Python)**:

```python
import argparse, os, logging

def configure_logging(args):
    verbose = int(args.verbose if args.verbose is not None else os.environ.get("VERBOSE", 1))
    debug   = int(args.debug   if args.debug   is not None else os.environ.get("DEBUG",   0))

    level_map = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG, 3: logging.DEBUG}
    log_level = level_map[min(verbose, 3)]

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),           # console
            logging.FileHandler(log_file_path()),  # file (always)
        ]
    )

    if debug >= 3 or verbose >= 3:
        enable_trace_logging()  # deep payloads, HTTP bodies, stack context
```

**Example (Node.js/TypeScript)**:

```typescript
const verboseIdx = process.argv.indexOf('--verbose');
const verbose = parseInt(
  verboseIdx !== -1 ? process.argv[verboseIdx + 1]
  : process.env.VERBOSE ?? '1'
);

const logger = winston.createLogger({
  level: ['error', 'info', 'debug', 'silly'][Math.min(verbose, 3)],
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: logFilePath() }),
  ],
});
```

---

## Log File Location

### Standard directory

All projects must write log files to:

```
<project-root>/logs/
```

Create this directory automatically at startup — never require UAT to create it manually.

### File naming convention

```
logs/<service>-<YYYY-MM-DD>.log          ← standard output (errors + info)
logs/<service>-debug-<YYYY-MM-DD>.log    ← debug output (when --debug >= 1)
logs/<service>-trace-<YYYY-MM-DD>.log    ← trace output (when --verbose=3 or --debug=3)
```

Replace `<service>` with the project or service name (lowercase, hyphens).

### `.gitignore` entry

```
logs/
```

Add this to `.gitignore`. Log files are runtime artifacts, not source — but UAT must have access to them via the known path.

### Automatic creation

```python
from pathlib import Path

def log_file_path(service: str = "app", level: str = "main") -> Path:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    suffix = "" if level == "main" else f"-{level}"
    return logs_dir / f"{service}{suffix}-{date_str}.log"
```

Never raise an error if `logs/` doesn't exist — create it. Never require UAT to configure the log path.

---

## What to Log at Each Level

### `error` (always on)

```python
logger.error("Upload failed", exc_info=True, extra={"file": path, "attempt": n})
```

- Exceptions with full stack trace
- Data integrity failures
- External service unreachable after retries

### `info` (default)

```python
logger.info("Processing started", extra={"input_count": len(items), "config": cfg.name})
```

- Start/stop of major operations
- Counts, durations, summary statistics
- Configuration values at startup

### `debug` (--debug 1+)

```python
logger.debug("Resolved path", extra={"raw": raw_path, "resolved": str(resolved)})
```

- Intermediate computed values
- Branch decisions with context
- Retry attempts with reason

### `trace` (--verbose 3 or --debug 3)

```python
logger.log(TRACE, "API response", extra={"status": resp.status, "body": resp.text[:2000]})
```

- Full request/response bodies (truncated at 2000 chars)
- Timing at every step
- All inputs and outputs per function call

---

## UAT Log Submission

When UAT submits a bug report, they should include:

1. **Run command** — exact CLI invocation with `--verbose` and `--debug` flags used
2. **Log files** — attach or reference files from `logs/`:
   - Standard log: `logs/<service>-<date>.log`
   - Debug log (if applicable): `logs/<service>-debug-<date>.log`
3. **Environment** — OS, Python/Node version, any relevant env vars

### UAT recommended invocation for investigation

```bash
# Maximum visibility for root cause analysis
<command> [args] --verbose 3 --debug 3
# Logs will appear in logs/<service>-<date>.log and logs/<service>-trace-<date>.log
```

### Bug report template addition

Add to the UAT scenario "Actual Results" section when logs are relevant:

```markdown
**Log artifacts**:
- `logs/myservice-2026-03-25.log` (standard)
- `logs/myservice-trace-2026-03-25.log` (trace, --verbose 3)

**Relevant log lines**:

    [ERROR] myservice: Upload failed: ConnectionResetError [attempt 3/3]
    [TRACE] myservice: HTTP POST /upload → status=500, body={"error":"timeout"}
```

---

## Pre-Commit Checklist Additions

- [ ] `logs/` is in `.gitignore`
- [ ] `logs/` directory is created automatically at startup (no manual step required)
- [ ] `--verbose` and `--debug` CLI flags (and `VERBOSE`/`DEBUG` env vars) are implemented
- [ ] Structured logger is used throughout (no bare `print()` for operational output)

---

## Related

- [UAT Testing Guide](../processes/uat-testing-guide.md) — how UAT references log artifacts
- [Pre-Commit Verification](pre-commit-verification.md) — logging checklist items
- [Code Quality Standards](code-quality-standards.md) — distinction between structured logging and debug prints
