# AI Container Intelligence Report

## Summary
- Total findings: 1
- Info: 0
- Critical: 0
- High: 1
- Medium: 0
- Low: 0

## Policy Impact
- Blocking findings: 1
- Advisory findings: 0
- Blocking threshold: CRITICAL
- Blocking rule IDs: DF004
- CI recommendation: FAIL

## Findings
1. [HIGH] DF004 - Container configured to run as root
   - Policy: BLOCKING
   - Source: dockerfile-review
   - Location: tmp-policy-gate\Dockerfile.root.nobom:2
   - Detail: Running as root increases container attack surface.
   - Remediation: Use a non-root runtime user.
