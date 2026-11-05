# PR-002 — Load `.env` and split the requirements

**Status:** Proposed, not built (source: the deployment audit of 2026-11-04; requirement FR-16)

## Problem
`main_flow/http.py` never loads `.env` (no `python-dotenv`), so the catalogue has `dotenv = false` and the deployment tool has a special path for it. The requirements files list `ruff`, `black`, `mypy`, `pytest` and `httpx` next to the runtime packages, and nothing is pinned.

## Proposal
1. Add `python-dotenv>=1.0.1` and load `.env` as stt and stepper do (`_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"`, `load_dotenv(dotenv_path=_ENV_FILE)` in `main_flow/http.py`; in a container that resolves to `/app/.env`), then set `dotenv = true` in the catalogue. `deployment/tests/test_env_file_only.py` (asserts `dotenv is False` for the microphone) and `deployment/docs/DEPLOYMENT.md` change in the same step.
2. Split the development tools into `requirements-dev.*` and keep the catalogue's `requirements` pointing at the runtime file; update the venv instructions in `CLAUDE.md`.
3. Pin with lower bounds (`>=`), the repository convention.

## Notes
Update `docs/configuration/environment-variables.md` (the note on `.env`), `docs/deployment/deployment.md`, `docs/security/security.md` (supply chain) and FR-16 when built.
