---
id: doc-engineering-006
title: Engineering Standards, Code Review, and Deployment Protocol
role_access: all
department: Engineering
version: 5.0
last_updated: 2026-03-01
---

# Engineering Standards, Code Review, and Deployment Protocol

## Section 1: Code Review and Pull Request Standards
Maintaining exceptional code quality and security is our shared engineering responsibility.
- Every pull request (PR) targeting `main` or release branches requires at least 2 approving reviews from peers on the relevant team CODEOWNERS list.
- Automated CI test suites must pass 100% with no skipped or flaky test exemptions.
- Code coverage must remain at or above 80% for all newly introduced backend code modules.
- PR descriptions must link to an active Jira issue and include a test plan detailing manual or automated verification steps.

## Section 2: Production Deployment Windows and Freezes
- Standard production deployment windows are Monday through Thursday, between 09:00 AM and 01:00 PM Pacific Time.
- Friday Deploy Freeze: No production deployments, schema migrations, or infrastructure modifications are permitted after 02:00 PM Pacific Time on Fridays.
- Weekend deploys are prohibited unless actively resolving a Sev-1 or Sev-2 production incident under Incident Commander authority.
- Major holiday freeze periods occur from December 20 through January 3 each year.

## Section 3: Observability and Incident Post-Mortems
- All production services must emit OpenTelemetry distributed traces and export metrics to Datadog.
- Alerts must be categorized into P1 (immediate pager), P2 (business hours), and P3 (ticket).
- Blameless post-mortems are mandatory for all Sev-1 and Sev-2 incidents and must be published within 72 hours of incident resolution.
