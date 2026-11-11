# Documentation of microphone_microservice

| Document | Content |
|---|---|
| [architecture/architecture.md](architecture/architecture.md) | Layers, package map, control flow, ports, the utterance cutting, debt |
| [api/api.md](api/api.md) | Routes, the envelope, the event stream, status codes |
| [configuration/environment-variables.md](configuration/environment-variables.md) | Every variable, default, rule and where else it is documented |
| [operations/monitoring.md](operations/monitoring.md) | Probes, shutdown, logs, tracing, what is absent |
| [requirements/requirements.md](requirements/requirements.md) | Functional and non-functional requirements with their status |
| [security/security.md](security/security.md) | Access, privacy of the captured audio, secrets, supply chain |
| [deployment/deployment.md](deployment/deployment.md) | How the deployment tool runs it; Windows, Linux, Docker |
| [tasks/README.md](tasks/README.md) | The task plan: protocol, baseline definition of done, board; [tasks/ORDER.md](tasks/ORDER.md) is the order to follow, with the state and the last update of every task |
| [setup/00_README.md](setup/00_README.md) | The project context in 17 ordered sub-forms (identity, purpose, scope, services, inputs and outputs, domain, technology, architecture, runtime, quality, decisions, risks, sources, work items) |
| [setup/questionnaires/](setup/questionnaires/00_README.md) | Questions for the maintainer; [Q01](setup/questionnaires/Q01_open-questions.md) holds the ones that stop tasks |
| [decisions/](decisions/) | Architecture decision records (ADR-001 to ADR-007) |
| [proposals/](proposals/) | Changes proposed and not built (PR-001 simulated backend, PR-002 `.env` and requirements) |
| [deployment_audit/microphone.md](deployment_audit/microphone.md) | Audit of 2026-11-04 from the deployment side: the source of the proposals |
| [architecture/PYTHON_MIGRATION_PLAN.md](architecture/PYTHON_MIGRATION_PLAN.md) | Historical plan of the refactor (executed) |
| `old/` | Legacy docs of the pre-refactor design (stale; do not trust) |

The rule that keeps these documents true is in [../CLAUDE.md](../CLAUDE.md): no change is finished until the documents that describe it are updated.
