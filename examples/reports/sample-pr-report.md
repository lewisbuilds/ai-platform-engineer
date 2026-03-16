# AI Container Intelligence Report

## Summary
- Total findings: 2
- Info: 0
- Critical: 0
- High: 1
- Medium: 1
- Low: 0

## Policy Impact
- Blocking findings: 1
- Advisory findings: 1
- Blocking threshold: CRITICAL
- Blocking rule IDs: DF004
- CI recommendation: FAIL

## Remediation Summary
1. [BLOCKING] (1 finding(s)) Use a non-root runtime user.
2. [ADVISORY] (1 finding(s)) Prefer COPY unless ADD-specific behavior is required.

## Findings
1. [HIGH] DF004 - Container configured to run as root
	- Policy: BLOCKING
	- Source: dockerfile-review
	- Location: Dockerfile:8
	- Detail: Running as root increases container attack surface.
	- Remediation: Use a non-root runtime user.
2. [MEDIUM] DF005 - ADD instruction used
	- Policy: ADVISORY
	- Source: dockerfile-review
	- Location: Dockerfile:10
	- Detail: ADD can have implicit behaviors that reduce clarity.
	- Remediation: Prefer COPY unless ADD-specific behavior is required.
