# Questionnaires

Decision questionnaires for the maintainer, in the format of `dynamics_microservice` (`docs/questionnaires/`). Each question gives a **recommended** answer; write yours after `A:`. `UNKNOWN`, `NOT APPLICABLE` and `LATER` are valid answers. **Never write secrets.** The newest answer wins. When a question is answered, process it in the same change: the task's *Resolution*, the ADR (new or a dated update), the requirement and the row below.

| File | Subject | State |
|---|---|---|
| [Q01_open-questions.md](Q01_open-questions.md) | What the documentation could not decide from the code: the simulated backend, `.env` loading, the meter default, the stale folders, the env files, the hardware session | Awaiting the maintainer (no answer recorded) |

Newer questionnaire for the deployment work: [Q02_deployment-readiness.md](Q02_deployment-readiness.md) (answered 2026-11-09 "Recommended" for all nine; it re-asks Q01-1 to Q01-4, which it supersedes).
