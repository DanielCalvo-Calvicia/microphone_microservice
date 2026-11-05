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
| [decisions/](decisions/) | Architecture decision records (ADR-001 to ADR-005) |
| [proposals/](proposals/) | Changes decided or proposed and not built (PR-001, PR-002) |
| [deployment_audit/microphone.md](deployment_audit/microphone.md) | Audit of 2026-11-04 from the deployment side: the source of the proposals |
| [architecture/PYTHON_MIGRATION_PLAN.md](architecture/PYTHON_MIGRATION_PLAN.md) | Historical plan of the refactor (executed) |
| `old/` | Legacy docs of the pre-refactor design (stale) |

The rule that keeps these documents true is in [../CLAUDE.md](../CLAUDE.md): no change is finished until the documents that describe it are updated.
