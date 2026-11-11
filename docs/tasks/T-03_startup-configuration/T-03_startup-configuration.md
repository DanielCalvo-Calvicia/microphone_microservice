# T-03 — Start-up configuration

| | |
|---|---|
| Status | done |
| Kind | epic |
| Depends on | — |
| Blocks | — |
| Record | [PR-002](../../proposals/PR-002-dotenv-and-requirements-split.md), requirement FR-16, risks 3 and 4 of `docs/setup/14_risks-and-debt.md` |

## Goal

Make the way the service starts and installs match the rest of the workspace: it loads its `.env` like stt and stepper, its requirements separate what runs from what develops, and its versions have lower bounds.

## Order

T-03.2 (requirements split, no other repository) first, because it needs no decision. T-03.3 (the maintainer's answer about changing `deployment`) then T-03.1 (load `.env`), which must land together with the change in `deployment`.

## Exit criteria

- `main_flow/http.py` loads the `.env` next to the repository root when it exists; a missing file is not an error; the process environment wins over the file.
- `requirements.windows.txt` and `requirements.linux.txt` hold only what the service needs to run, with lower bounds; `requirements-dev.windows.txt` and `requirements-dev.linux.txt` add the test and lint tools.
- `deployment/config/catalogue.toml` has `dotenv = true` for the microphone, `deployment/tests/test_env_file_only.py` and `deployment/docs/DEPLOYMENT.md` agree, and the deployment suite passes.
- The documents of the table in `CLAUDE.md` are updated; FR-16 is `Done`; PR-002 has a dated note.

## Notes

stt and stepper are the reference: `_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"` and `load_dotenv(dotenv_path=_ENV_FILE)` in their `main_flow/http.py`; in a container that resolves to `/app/.env`, where the deployment tool bind-mounts the file. Read them before writing, do not edit them.

## Update 2026-11-09 (plan revision 2)

The `deployment` side of this epic (the catalogue flag, three tests, the manual) is **T-06.1**, in the new epic T-06; the epic closes when T-03.1 to T-03.3 **and** T-06.1 are done. The pins follow Q02-7.
