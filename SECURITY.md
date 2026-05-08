# Security policy

CLAD is a methodology repository. Most files are markdown, templates, and
agent guides. The only executable code is the optional Java reference
profile under [`reference-impl/java-micronaut-jena/`](reference-impl/java-micronaut-jena/).

## Reporting a vulnerability

If you believe you have found a security vulnerability — whether in the
methodology, the CI scripts, or the reference implementation — please
**do not file a public issue**.

Open a private security advisory:
<https://github.com/abratto/clad/security/advisories/new>

Please include:

- A description of the issue and its impact.
- Steps to reproduce, or a minimal proof-of-concept.
- The commit SHA you observed it on.

You can expect an initial acknowledgement within a week. Coordinated
disclosure timing will be agreed before any public write-up.

## Supported versions

This is a seed repository at pre-1.0. Only the latest commit on `main`
is supported.

## Out of scope

- Vulnerabilities in third-party dependencies (those are tracked by
  Dependabot and addressed via normal PRs).
- Issues in *forks* or downstream projects that adopted CLAD as a
  starter — please report those to the fork's maintainers.
- The CI environment itself (GitHub Actions runners, GitHub-hosted
  services) — report to GitHub via their own security channels.
