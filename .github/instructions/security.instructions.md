---
applyTo: "**/*"
---
# Security Standards (NON-NEGOTIABLE)

- All user-supplied input MUST be validated and sanitized at system boundaries
- Parameterized queries or equivalent safe access patterns MUST be used for all data access
- Secrets, credentials, and connection strings MUST NOT be hardcoded or committed
- Dependencies MUST be scanned for known vulnerabilities before committing
- Internal error details MUST NOT be surfaced in external-facing responses

For full details, see `.github/docs/philosophy/security-vulnerability-management.md`
