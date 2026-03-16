# AI Container Intelligence Report

## Summary
- Total findings: 2
- Info: 0
- Critical: 1
- High: 1
- Medium: 0
- Low: 0

## Policy Impact
- Blocking findings: 2
- Advisory findings: 0
- Blocking threshold: CRITICAL
- Blocking rule IDs: DF001, DF004
- CI recommendation: FAIL

## Findings
1. [CRITICAL] DF001 - Missing FROM instruction
   - Policy: BLOCKING
   - Source: dockerfile-review
   - Location: G:\projects\AI Platform Engineer\tmp-policy-gate\Dockerfile.root
   - Detail: Dockerfile must declare at least one base image.
   - Remediation: Add a pinned and trusted FROM image.
2. [HIGH] DF004 - Container configured to run as root
   - Policy: BLOCKING
   - Source: dockerfile-review
   - Location: G:\projects\AI Platform Engineer\tmp-policy-gate\Dockerfile.root:2
   - Detail: Running as root increases container attack surface.
   - Remediation: Use a non-root runtime user.
