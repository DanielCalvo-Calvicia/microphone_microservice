# Setup — intake sub-forms (microphone_microservice)

The project context, split into ordered sub-forms in the format of `dynamics_microservice` (`docs/setup/`). Read or fill them **in numeric order**: each one builds on the previous ones (what the project is, who it talks to, how it is built, how it runs, what is decided and pending). Written on 2026-11-05 from the code, the git history, the deployment tool and the deployment audit of 2026-11-04.

**Rules**
- Never invent answers. Unknown: `UNKNOWN`. Not relevant: `NOT APPLICABLE`. Something that only the maintainer can say: it is a question in [questionnaires/](questionnaires/00_README.md), not an answer.
- No secrets, tokens or credentials in any file. The `.env`, `.env.staging` and `.env.production` files were not opened.
- Every fact comes from a file of this repository, the workspace (`../CLAUDE.md`, `../deployment`, `../contracts`) or a commit; where it does not, it says so.
- **Not pushed anywhere.** The `.engram/` folder of this repository is stale (see file 15) and Engram Cloud is not used for this project; nothing here was sent to it.

## Order

| # | File | Content |
|---|---|---|
| 01 | [01_identity.md](01_identity.md) | Name, repository, owner, language, status |
| 02 | [02_purpose.md](02_purpose.md) | The problem, the objective, responsibilities and non-responsibilities |
| 03 | [03_business-context-and-scope.md](03_business-context-and-scope.md) | Where it sits in OBLIVION, what is in and out of scope |
| 04 | [04_glossary-and-conventions.md](04_glossary-and-conventions.md) | Terms, naming, language, commits |
| 05 | [05_external-services.md](05_external-services.md) | Who calls it, what it calls, the hardware |
| 06 | [06_inputs-and-outputs.md](06_inputs-and-outputs.md) | Routes, events, configuration, logs |
| 07 | [07_data-and-persistence.md](07_data-and-persistence.md) | Data held, privacy, retention |
| 08 | [08_domain-modeling.md](08_domain-modeling.md) | Entities, value objects, operations, errors |
| 09 | [09_technology.md](09_technology.md) | Language, libraries, versions, constraints |
| 10 | [10_architecture.md](10_architecture.md) | Layers, dependency rules, ports |
| 11 | [11_runtime-and-deployment.md](11_runtime-and-deployment.md) | How it runs and is deployed |
| 12 | [12_quality-and-operations.md](12_quality-and-operations.md) | Tests, lint, logging, availability |
| 13 | [13_decisions-and-overrides.md](13_decisions-and-overrides.md) | Decisions taken and overrides of the workspace standard |
| 14 | [14_risks-and-debt.md](14_risks-and-debt.md) | Risks, limits and known debt |
| 15 | [15_sources-contradictions-questions.md](15_sources-contradictions-questions.md) | Sources, contradictions found, open questions |
| 16 | [16_work-items.md](16_work-items.md) | The work items, one per epic of `docs/tasks` |
| 17 | [17_validation-checklist.md](17_validation-checklist.md) | Checklist for this documentation |

Open questions that block a decision are in file 15 and become work items in file 16 and the `awaiting-user` tasks of [../tasks/ORDER.md](../tasks/ORDER.md); do not duplicate them elsewhere.
