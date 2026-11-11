# T-06 — Deployment tool changes (the `deployment` repository)

| | |
|---|---|
| Status | done |
| Kind | epic |
| Depends on | T-02.1, T-03.3 (each leaf names its own other dependencies) |
| Blocks | T-07 |

## Goal

Change the deployment tool so that the microphone can be deployed on a machine **without** a sound card and prove it, loads its `.env` like the other services, and so that the manual says the same as the catalogue. Today `deploy` reports the service as failed after the 15 s grace when `/available` is false, and `update` rolls back a healthy commit (F6); the catalogue says `dotenv = false` and three tests depend on it (F8).

## Rules for this epic

- `deployment` is its own repository with its own `CLAUDE.md`: **read `deployment/CLAUDE.md` before editing anything** (layered layout, every external command through `Shell`, dry-run without side effects, tests for the install path, `docs/DEPLOYMENT.md` kept in step with each `.env.example`).
- The edits are made in `D:\Hobbys\IA\OBLIVION\deployment`, not in this repository. This epic lives here because its cause and its acceptance are the microphone's. Do not commit or push in either repository unless asked.
- The speaker plan edits the same `config/catalogue.toml` and `docs/DEPLOYMENT.md` (F14): read `git status` and `git diff` of a file before editing it and keep to your own lines; microphone first, then speaker.
- The deployment tests are run with the brain venv from `deployment/`, in the background (about 190 s): `..\brain_microservice\windows\Scripts\python.exe -m pytest tests -q`. They use the fake `Shell` and `--dry-run`: no image is built in this epic (that is T-07).
- Never touch `deployment/config/local/`; use `--config <a throw-away config folder>` for `validate` and `env`.

## Subtasks

| Order | Task | Kind | State |
|---|---|---|---|
| 1 | [T-06.1 `dotenv = true` and the tests that name the microphone](T-06.1_dotenv-in-the-catalogue.md) | code | blocked (T-03.1) |
| 2 | [T-06.2 The `sim` preset in the catalogue](T-06.2_sim-preset.md) | code | blocked (T-02.3) |
| 3 | [T-06.3 Readiness on a machine without a device](T-06.3_readiness-without-a-device.md) | code | blocked (T-06.2) |
| 4 | [T-06.4 Docker on Windows for a microphone on `sim`](T-06.4_docker-on-windows-with-sim.md) | code | awaiting-user |
| 5 | [T-06.5 Inventory and manual](T-06.5_inventory-and-manual.md) | docs | blocked (T-06.1, T-06.2) |

## Exit criteria

The catalogue entry of the microphone says `dotenv = true` and (if Q02-1 says so) carries the `sim` preset; a layout with the microphone on `sim` passes the readiness check without a device and the tool prints the reason; a layout on `real` without a device still fails as before; `env_inventory.py --check` passes; `deployment/docs/DEPLOYMENT.md`, `deployment/CLAUDE.md` and `docs/deployment/deployment.md` of this repository say the same; the deployment suite passes.
