# Enterprise Quality & NFR Audit — 2026-07-02

Automated audit of `VilnaCRM-Org/infrastructure-template` against the quality attributes from
[Wikipedia's List of system quality attributes](https://en.wikipedia.org/wiki/List_of_system_quality_attributes),
plus an AI-native autonomous development readiness dimension.

- **Attributes audited:** 98 across 11 clusters
- **Average score:** 3.86/5
- **Distribution:** 9× 5/5, 67× 4/5, 21× 3/5, 1× 2/5
- **Attributes at 5/5:** 9
- **GitHub issues filed (one per attribute below 5/5):** 89 (#43–#131, label `enhancement`)

Scoring bar: 5 = fully addressed, institutionalized and enforced by automation; 4 = solid with minor
concrete gaps; 3 = partially addressed; 2 = ad-hoc; 1 = absent. Every attribute scoring below 5/5 has a
dedicated GitHub issue with tasks and acceptance criteria to reach 5/5.

## Cluster summary

| Cluster | Attributes | Average | At 5/5 |
|---|---|---|---|
| Security & Trust | 8 | 4.00 | 0 |
| Reliability & Resilience | 14 | 3.50 | 0 |
| Maintainability & Code Quality | 13 | 4.38 | 5 |
| Testability & Correctness | 11 | 4.36 | 4 |
| Performance & Scalability | 7 | 3.14 | 0 |
| Portability & Deployability | 10 | 3.70 | 0 |
| Usability & Developer Experience | 10 | 3.80 | 0 |
| Configurability & Operability | 9 | 3.78 | 0 |
| Observability & Diagnosability | 5 | 3.80 | 0 |
| Governance, Process & Compliance | 6 | 3.67 | 0 |
| AI-Native Autonomous Development Readiness | 5 | 4.00 | 0 |

## Full scorecard

### Security & Trust

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| accountability | 4/5 | [#43](https://github.com/VilnaCRM-Org/infrastructure-template/issues/43) | No CODEOWNERS to assign review ownership; Branch protection and required checks are not codified |
| auditability | 4/5 | [#45](https://github.com/VilnaCRM-Org/infrastructure-template/issues/45) | CHANGELOG.md is empty; No retention policy for guardrail evidence artifacts |
| confidentiality | 4/5 | [#46](https://github.com/VilnaCRM-Org/infrastructure-template/issues/46) | Gitleaks config has no repo-specific rules or allowlist governance; GitHub push protection / secret scanning not part of the documented baseline |
| integrity | 4/5 | [#48](https://github.com/VilnaCRM-Org/infrastructure-template/issues/48) | Releases are not attested or signed; Signed-commit enforcement is absent from the governance contract |
| safety | 4/5 | [#51](https://github.com/VilnaCRM-Org/infrastructure-template/issues/51) | Destructive gate's critical-resource list omits common stateful services; No backup/restore or state-recovery runbook |
| securability | 4/5 | [#53](https://github.com/VilnaCRM-Org/infrastructure-template/issues/53) | Policy pack covers a limited AWS resource surface |
| vulnerability | 4/5 | [#55](https://github.com/VilnaCRM-Org/infrastructure-template/issues/55) | Dependabot covers only pulumi/ pip; actions, Docker, and root Python deps get no automated updates; SECURITY.md lacks a real disclosure and response policy; No vulnerability scanning of the built Docker workspace image |
| credibility | 4/5 | [#57](https://github.com/VilnaCRM-Org/infrastructure-template/issues/57) | Copy-paste artifacts and placeholders in trust-facing documents; No Scorecard/attestation badges or published quality claims for consumers |

### Reliability & Resilience

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| availability | 3/5 | [#44](https://github.com/VilnaCRM-Org/infrastructure-template/issues/44) | No Docker image caching in CI creates external-endpoint availability dependency; Template encodes no availability patterns for downstream infrastructure; No availability monitoring of scheduled automation |
| dependability | 4/5 | [#47](https://github.com/VilnaCRM-Org/infrastructure-template/issues/47) | Branch-protection/required-checks configuration is manual and unverified; Scheduled automation failures are silent |
| durability | 3/5 | [#49](https://github.com/VilnaCRM-Org/infrastructure-template/issues/49) | No backup-retention or versioning policies for stateful resources; Pulumi state durability requirements are undocumented and unenforced |
| degradability | 4/5 | [#50](https://github.com/VilnaCRM-Org/infrastructure-template/issues/50) | Degraded modes exit green indefinitely without escalation |
| failure transparency | 4/5 | [#52](https://github.com/VilnaCRM-Org/infrastructure-template/issues/52) | No push notification path for scheduled and release automation failures; SECURITY.md ships a 'TBD' placeholder |
| fault-tolerance | 3/5 | [#54](https://github.com/VilnaCRM-Org/infrastructure-template/issues/54) | No retry handling for transient failures in Pulumi CI operations; IAM validation parallelism has no per-policy fault isolation |
| recoverability | 3/5 | [#56](https://github.com/VilnaCRM-Org/infrastructure-template/issues/56) | No documented Pulumi state backup/restore or rollback runbook; No definition of recovery objectives (RTO/RPO) for template consumers |
| redundancy | 3/5 | [#58](https://github.com/VilnaCRM-Org/infrastructure-template/issues/58) | No redundancy requirements encoded for downstream AWS resources; Single-region CI/guardrail configuration with no fallback |
| reliability | 4/5 | [#59](https://github.com/VilnaCRM-Org/infrastructure-template/issues/59) | Per-job image rebuilds make CI reliability hostage to external endpoints; No flaky-test policy or detection for the real-CLI integration suite |
| resilience | 3/5 | [#61](https://github.com/VilnaCRM-Org/infrastructure-template/issues/61) | Disruption-recovery paths for the shared backend and CI are undocumented and untested; No periodic exercise of failure paths (guardrail 'fire drill') |
| robustness | 4/5 | [#62](https://github.com/VilnaCRM-Org/infrastructure-template/issues/62) | Unhandled exceptions in event/artifact parsing produce raw tracebacks instead of diagnostics; No property-based testing on preview-artifact parsers |
| stability | 4/5 | [#64](https://github.com/VilnaCRM-Org/infrastructure-template/issues/64) | No documented template-sync conflict/ignore strategy for downstream repos; No breaking-change/compatibility policy for template releases |
| survivability | 4/5 | [#66](https://github.com/VilnaCRM-Org/infrastructure-template/issues/66) | Pulumi `protect` resource option not used or recommended for critical resources; No post-incident survival plan for state or resource loss |
| self-sustainability | 3/5 | [#68](https://github.com/VilnaCRM-Org/infrastructure-template/issues/68) | Dependabot covers only pip in pulumi/, leaving actions, Docker, and the uv root project unmanaged; Hand-pinned Dockerfile tool versions have no automated update path; Single-person review bottleneck in automated dependency flow |

### Maintainability & Code Quality

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| analyzability | 5/5 | — | — |
| composability | 4/5 | [#60](https://github.com/VilnaCRM-Org/infrastructure-template/issues/60) | No reusable workflow or composite action for the shared Docker-workspace bootstrap; No demonstration of composing multiple Pulumi components |
| evolvability | 4/5 | [#63](https://github.com/VilnaCRM-Org/infrastructure-template/issues/63) | Dependabot ignores GitHub Actions, Docker, the root uv project, and the policy runtime; Duplicate dependency declarations have already diverged; Root CHANGELOG.md is an empty placeholder |
| extensibility | 4/5 | [#65](https://github.com/VilnaCRM-Org/infrastructure-template/issues/65) | No worked example of extending the Pulumi program with a real resource; No documented recipe for adding a new CrossGuard policy |
| maintainability | 5/5 | — | — |
| modifiability | 4/5 | [#67](https://github.com/VilnaCRM-Org/infrastructure-template/issues/67) | Quadruplicated inline bash in the Makefile's Pulumi lifecycle targets |
| modularity | 5/5 | — | — |
| orthogonality | 5/5 | — | — |
| repairability | 4/5 | [#69](https://github.com/VilnaCRM-Org/infrastructure-template/issues/69) | No Pulumi state backup and recovery runbook |
| reusability | 4/5 | [#70](https://github.com/VilnaCRM-Org/infrastructure-template/issues/70) | No template bootstrap/rename automation for downstream repos; Template-sync uses force-push PRs with no documented downstream customization contract |
| serviceability | 4/5 | [#71](https://github.com/VilnaCRM-Org/infrastructure-template/issues/71) | SECURITY.md is a placeholder; No release support/versioning policy for template consumers |
| simplicity | 4/5 | [#73](https://github.com/VilnaCRM-Org/infrastructure-template/issues/73) | Redundant dependency declarations and intricate venv bootstrap machinery |
| understandability | 5/5 | — | — |

### Testability & Correctness

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| accuracy | 4/5 | [#72](https://github.com/VilnaCRM-Org/infrastructure-template/issues/72) | Destructive-diff critical-resource list omits common critical AWS types |
| correctness | 4/5 | [#74](https://github.com/VilnaCRM-Org/infrastructure-template/issues/74) | Repo-wide ty rule suppressions weaken the type-correctness gate |
| demonstrability | 4/5 | [#75](https://github.com/VilnaCRM-Org/infrastructure-template/issues/75) | No machine-readable test or coverage artifacts from PR test workflows; Committed CHANGELOG.md is empty despite release automation |
| determinability | 4/5 | [#77](https://github.com/VilnaCRM-Org/infrastructure-template/issues/77) | Drift-detection outcomes are not persisted or surfaced beyond job logs |
| fidelity | 4/5 | [#78](https://github.com/VilnaCRM-Org/infrastructure-template/issues/78) | Guardrails are never exercised against a program that declares real AWS resources |
| precision | 5/5 | — | — |
| predictability | 5/5 | — | — |
| provability | 4/5 | [#80](https://github.com/VilnaCRM-Org/infrastructure-template/issues/80) | Mutation testing excludes the policy pack and CI guardrail scripts |
| repeatability | 5/5 | — | — |
| reproducibility | 4/5 | [#82](https://github.com/VilnaCRM-Org/infrastructure-template/issues/82) | CI rebuilds the workspace image every run with an unpinned apt layer |
| testability | 5/5 | — | — |

### Performance & Scalability

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| distributability | 4/5 | [#76](https://github.com/VilnaCRM-Org/infrastructure-template/issues/76) | No template-sync exclusion contract for downstream customizations; No published prebuilt toolchain image for consumers |
| effectiveness | 4/5 | [#79](https://github.com/VilnaCRM-Org/infrastructure-template/issues/79) | Template ships guardrails but no reusable infrastructure components; Policy pack coverage limited to a hardcoded set of resource families |
| efficiency | 3/5 | [#81](https://github.com/VilnaCRM-Org/infrastructure-template/issues/81) | Docker toolchain image rebuilt from scratch in every CI job; pulumi-local.yml duplicates the entire PR battery; No path-based triggering for expensive workflows |
| elasticity | 2/5 | [#83](https://github.com/VilnaCRM-Org/infrastructure-template/issues/83) | No elastic infrastructure patterns or scaling guidance in the template; Ephemeral per-PR stack lifecycle is documented but not automated |
| responsiveness | 3/5 | [#84](https://github.com/VilnaCRM-Org/infrastructure-template/issues/84) | Per-job image rebuild delays first feedback on every check; No monitoring of CI feedback-time as a managed metric |
| scalability | 3/5 | [#86](https://github.com/VilnaCRM-Org/infrastructure-template/issues/86) | Serial per-stack preview and drift loops break beyond a handful of stacks; Single-account, single-backend assumption with no multi-account scaling path; No composable component layer for growing real infrastructure |
| timeliness | 3/5 | [#88](https://github.com/VilnaCRM-Org/infrastructure-template/issues/88) | Dependabot covers only pulumi/requirements.txt, not the real dependency surfaces; ARG-pinned toolchain versions in the Dockerfile have no update automation; Nightly drift detection silently no-ops until repo variables are set |

### Portability & Deployability

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| compatibility | 4/5 | [#85](https://github.com/VilnaCRM-Org/infrastructure-template/issues/85) | Divergent Pulumi version bounds between pulumi/requirements.txt and pyproject.toml; Narrow and untested Python version window; make doctor does not verify the documented Docker Compose version floor |
| deployability | 4/5 | [#87](https://github.com/VilnaCRM-Org/infrastructure-template/issues/87) | No reference deploy (pulumi up) workflow or environment-promotion pipeline; Only a dev stack configuration is committed; no per-environment stack exemplars |
| installability | 4/5 | [#89](https://github.com/VilnaCRM-Org/infrastructure-template/issues/89) | No bootstrap/rename automation for template consumers; No .templatesyncignore to protect consumer customizations after install |
| interchangeability | 3/5 | [#90](https://github.com/VilnaCRM-Org/infrastructure-template/issues/90) | Policy pack and guardrails have no extension seam for non-AWS providers; Cloud-provider substitution is undocumented despite a provider-neutral core |
| interoperability | 4/5 | [#92](https://github.com/VilnaCRM-Org/infrastructure-template/issues/92) | SBOM and provenance are nightly artifacts, not release assets; Coverage results are not exported in a standard machine-readable format |
| mobility | 4/5 | [#94](https://github.com/VilnaCRM-Org/infrastructure-template/issues/94) | arm64 image path is defined but never built or tested in CI; No devcontainer/Codespaces configuration despite a fully containerized workflow |
| portability | 4/5 | [#96](https://github.com/VilnaCRM-Org/infrastructure-template/issues/96) | Windows/WSL host support is undocumented and unverified; CI validates portability claims on a single OS/architecture only |
| seamlessness | 4/5 | [#98](https://github.com/VilnaCRM-Org/infrastructure-template/issues/98) | No prebuilt/published dev image, so first contact requires a full multi-stage build; GITHUB_TOKEN hand-off for Pulumi plugin downloads is a manual seam |
| ubiquity | 3/5 | [#100](https://github.com/VilnaCRM-Org/infrastructure-template/issues/100) | Build-time internet dependencies block restricted-network adoption; Hard GitHub coupling with no portability note for other platforms |
| upgradability | 3/5 | [#102](https://github.com/VilnaCRM-Org/infrastructure-template/issues/102) | Dependabot ignores the dependencies that actually drive the build; Toolchain versions baked into the Dockerfile have no automated refresh path; No upgrade/migration guidance for downstream template consumers |

### Usability & Developer Experience

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| accessibility | 3/5 | [#91](https://github.com/VilnaCRM-Org/infrastructure-template/issues/91) | No devcontainer/Codespaces support for developers who cannot run the Compose workspace locally; Color-only, non-configurable terminal output in make help and CI logs; No automated Markdown quality/link checking for the docs handbook |
| convenience | 4/5 | [#93](https://github.com/VilnaCRM-Org/infrastructure-template/issues/93) | No pre-commit hooks or host-native fast path for trivial checks; No initialization/rename automation for template consumers |
| discoverability | 4/5 | [#95](https://github.com/VilnaCRM-Org/infrastructure-template/issues/95) | Empty CHANGELOG.md misleads consumers looking for release history; No CODEOWNERS file to route questions and reviews; Downstream adoption steps are scattered rather than indexed |
| familiarity | 4/5 | [#97](https://github.com/VilnaCRM-Org/infrastructure-template/issues/97) | Copy-pasted boilerplate from a different template in CONTRIBUTING.md and issue templates; Conventional-commit requirement is undocumented and unenforced |
| interactivity | 4/5 | [#99](https://github.com/VilnaCRM-Org/infrastructure-template/issues/99) | Pulumi preview and destructive-diff results not surfaced on the PR conversation; Nightly quality and guardrail failures produce no proactive signal |
| intuitiveness | 4/5 | [#101](https://github.com/VilnaCRM-Org/infrastructure-template/issues/101) | Three-way env file scheme (.env / .env.empty / .env.dist) is confusing; Aggregate target test-battery is undocumented in make help |
| learnability | 4/5 | [#103](https://github.com/VilnaCRM-Org/infrastructure-template/issues/103) | Quick Start and example stack config reference a sample EC2 instance the program no longer creates; No end-to-end 'first deployment' tutorial for downstream teams |
| localizability | 3/5 | [#104](https://github.com/VilnaCRM-Org/infrastructure-template/issues/104) | Region and organization defaults are scattered and branded, with no single localization knob; No documented language policy for docs and user-facing strings |
| relevance | 4/5 | [#106](https://github.com/VilnaCRM-Org/infrastructure-template/issues/106) | Stale and placeholder content contradicts the template's polished core |
| usability | 4/5 | [#108](https://github.com/VilnaCRM-Org/infrastructure-template/issues/108) | Downstream repos inherit maximal quality gates with no documented tailoring path; First-run experience lacks automation for template-specific setup |

### Configurability & Operability

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| adaptability | 4/5 | [#105](https://github.com/VilnaCRM-Org/infrastructure-template/issues/105) | Narrow Python version window (>=3.10,<3.12) limits runtime adaptation; No reference infrastructure components to adapt from |
| administrability | 4/5 | [#107](https://github.com/VilnaCRM-Org/infrastructure-template/issues/107) | Branch protection and required checks are documented but not codified or verified; No CODEOWNERS for review routing |
| agility | 4/5 | [#109](https://github.com/VilnaCRM-Org/infrastructure-template/issues/109) | Dependabot misses github-actions, docker, and the root uv-managed Python project |
| configurability | 4/5 | [#110](https://github.com/VilnaCRM-Org/infrastructure-template/issues/110) | CI guardrail constants are hardcoded rather than configuration-driven; Stale example stack config (Pulumi.example.yaml) with unused keys |
| customizability | 3/5 | [#112](https://github.com/VilnaCRM-Org/infrastructure-template/issues/112) | Template-sync collides with downstream customization; no .templatesyncignore strategy; No downstream customization/extension guide |
| flexibility | 4/5 | [#114](https://github.com/VilnaCRM-Org/infrastructure-template/issues/114) | Docker Compose is effectively mandatory; the non-Docker path is untested; Guardrail stack is AWS-only without stated multi-cloud posture |
| manageability | 4/5 | [#115](https://github.com/VilnaCRM-Org/infrastructure-template/issues/115) | Empty committed CHANGELOG.md despite changelog-driven release automation; Scheduled drift/quality failures have no notification or issue-creation path |
| operability | 4/5 | [#117](https://github.com/VilnaCRM-Org/infrastructure-template/issues/117) | No state backup/restore or rollback runbook; Doctor and triage flows do not verify cloud/backend reachability |
| tailorability | 3/5 | [#119](https://github.com/VilnaCRM-Org/infrastructure-template/issues/119) | No post-clone tailoring checklist or bootstrap for org-specific values; Org-specific defaults hardwired in synced automation files |

### Observability & Diagnosability

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| debuggability | 4/5 | [#111](https://github.com/VilnaCRM-Org/infrastructure-template/issues/111) | make doctor only verifies Docker and the env file; No documented verbose/debug escalation for Pulumi and CI failures |
| inspectability | 4/5 | [#113](https://github.com/VilnaCRM-Org/infrastructure-template/issues/113) | Test, coverage, and quality gate jobs publish no inspectable artifacts; IAM validation inputs are never persisted as a CI artifact |
| observability | 3/5 | [#116](https://github.com/VilnaCRM-Org/infrastructure-template/issues/116) | No runtime observability patterns or guidance for downstream infrastructure; Policy pack observability enforcement stops at S3/LB access logs; No alerting channel for scheduled guardrail/drift failures |
| traceability | 4/5 | [#118](https://github.com/VilnaCRM-Org/infrastructure-template/issues/118) | Committed CHANGELOG.md is empty and never updated by automation; Conventional-commit format is not enforced in CI |
| transparency | 4/5 | [#120](https://github.com/VilnaCRM-Org/infrastructure-template/issues/120) | SECURITY.md is skeletal ('TBD') with no response SLA or supported-versions statement; No architecture decision records for major stack pivots |

### Governance, Process & Compliance

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| affordability | 3/5 | [#122](https://github.com/VilnaCRM-Org/infrastructure-template/issues/122) | No infrastructure cost-estimation gate despite docs claiming Infracost exists; Every CI job rebuilds the Docker workspace from scratch with no caching; Policy pack enforces no cost-relevant sizing or budget guardrails |
| autonomy | 4/5 | [#124](https://github.com/VilnaCRM-Org/infrastructure-template/issues/124) | Dependabot flow depends on one named human with no auto-merge; No CODEOWNERS for autonomous review routing |
| process capabilities | 4/5 | [#126](https://github.com/VilnaCRM-Org/infrastructure-template/issues/126) | Branch protection / required checks are documented but not codified; Conventional commits are relied on by autorelease but never enforced |
| producibility | 4/5 | [#127](https://github.com/VilnaCRM-Org/infrastructure-template/issues/127) | No published, signed canonical dev image; Releases ship without artifacts, SBOM, or attestation linkage |
| standards compliance | 3/5 | [#129](https://github.com/VilnaCRM-Org/infrastructure-template/issues/129) | SECURITY.md does not meet a real disclosure-policy standard; CONTRIBUTING.md is stale boilerplate from another template; Missing in-repo CODE_OF_CONDUCT.md and CODEOWNERS community-health files; Dependabot ecosystem coverage is incomplete |
| sustainability | 4/5 | [#131](https://github.com/VilnaCRM-Org/infrastructure-template/issues/131) | Manually pinned toolchain will rot without update automation; Low bus factor with no ownership or succession structure; No in-repo change history for template consumers |

### AI-Native Autonomous Development Readiness

| Attribute | Score | Issue | Key gaps |
|---|---|---|---|
| agent-readiness (AGENTS.md / machine-readable project knowledge) | 4/5 | [#121](https://github.com/VilnaCRM-Org/infrastructure-template/issues/121) | AGENTS.md drift is only enforced by one narrow substring test; No scoped agent context for high-friction subsystems |
| autonomous feedback loops (agents can run/verify all quality gates locally) | 4/5 | [#123](https://github.com/VilnaCRM-Org/infrastructure-template/issues/123) | Every quality gate requires a Docker daemon; no supported native execution mode; GitHub-native gates (CodeQL, Dependency Review, Scorecard) have no local approximation |
| machine-actionable quality gates (deterministic, self-explaining CI) | 4/5 | [#125](https://github.com/VilnaCRM-Org/infrastructure-template/issues/125) | Test and lint gates emit no machine-readable results; pip-audit --strict is a time-varying blocker with no documented exception path |
| agent-safe tooling (guardrails preventing destructive autonomous actions) | 4/5 | [#128](https://github.com/VilnaCRM-Org/infrastructure-template/issues/128) | AGENTS.md safety rules have no executable enforcement for local agent sessions; Destructive-diff gate is allowlist-scoped; unlisted resource types bypass review |
| docs-as-context (documentation optimized for LLM consumption) | 4/5 | [#130](https://github.com/VilnaCRM-Org/infrastructure-template/issues/130) | No markdown link-check or lint gate in CI; Docs-code alignment relies on brittle substring assertions instead of generated references |

## Method

Eleven parallel auditor agents each examined the repository evidence (workflows, Makefile, Pulumi program,
policy pack, test suites, docs) for one cluster of attributes and scored each attribute 1–5 with cited
justification and concrete gaps. Issue-filer agents then created one `enhancement` issue per attribute below
5/5, each following the repository feature-request format (Description / Tasks / Acceptance Criteria).
Re-run the audit after remediation to verify attributes re-score 5/5.
