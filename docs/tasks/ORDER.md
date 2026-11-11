# Task order

The order in which the tasks must be done, with the state of each one and the date its file was last updated. It follows the execution protocol of the [tasks README](README.md) (section 2): the first task that is `todo` and whose dependencies are `done`. Decisions that stop the chain are marked.

**Keep this file true:** every change to a task (a status, a dependency, a new task, an order change) updates this table, the board of the [tasks README](README.md) section 5 and the task file itself (see `CLAUDE.md`). The *Last updated* column is the date of the last change to the task file and is refreshed by the same change.

## States

| State | Meaning |
|---|---|
| Done | Implemented and verified (or, for a decision, taken and recorded) |
| Awaiting user | A decision needs the maintainer's answer; it stops the chain |
| Todo | Ready to start when its dependencies are done |
| Blocked | Waits for another task or for a decision |
| Postponed | Decided not to run yet (the Raspberry Pi and native Linux wait until the services work at 100 % on Windows, 2026-11-09); it does not block the Windows work |
| Recurring | Repeated after every change that touches the documents |

Written on 2026-11-05, revised on 2026-11-09 (plan revision 2: T-06 and T-07 added, T-04.3 and T-04.4 postponed). **Todo (next)** is the task to start now. Tasks marked *needs the maintainer* cannot be completed by the assistant alone. Three decisions stop most of the chain: **T-02.1** (Q02-1 to Q02-3), **T-03.3** (Q02-4) and **T-06.4** (Q02-6); until they are answered only T-03.2 can start.

## A. Done: capture and utterances (T-01), history

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 1 | [T-01](T-01_capture-and-utterances/T-01_capture-and-utterances.md) | Capture and utterances | epic | Done | built 2026-09-20 to 2026-10-05; the pre-roll was added 2026-11-09 (`fde20ad`, 142 tests); behaviour on a real microphone not re-checked since (T-04) | — | 2026-11-09 |

## B. Next

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 2 | [T-03.2](T-03_startup-configuration/T-03.2_requirements-split.md) | Split the requirements, pin what ran | code | Done | no decision needed except the pin style (Q02-7, recommended: exact, as stt); no other repository | — | 2026-11-10 |
| 3 | [T-02.1](T-02_simulated-backend/T-02.1_decisions.md) | Decisions: default, variable, signal | decision | Done | Q02-1 to Q02-3 (Q01-1 to Q01-3); stops T-02.2 to T-02.5 | — | 2026-11-09 |
| 4 | [T-02.2](T-02_simulated-backend/T-02.2_sim-capture-adapter.md) | The simulated capture adapter | code | Done | needs T-02.1 | T-02.1 | 2026-11-10 |
| 5 | [T-02.3](T-02_simulated-backend/T-02.3_wiring-and-config.md) | Wiring and configuration | code | Done | needs T-02.2; also the lazy import of `sounddevice` (F5) | T-02.2 | 2026-11-10 |
| 6 | [T-02.4](T-02_simulated-backend/T-02.4_tests.md) | Tests of the backend | code | Done | needs T-02.3 | T-02.3 | 2026-11-10 |
| 7 | [T-02.5](T-02_simulated-backend/T-02.5_deployment-and-pipeline.md) | Pipeline check with the real service on `sim` | code | Done | needs T-02.4 and T-06.2; the preset itself is T-06.2 | T-02.4, T-06.2 | 2026-11-10 |
| 8 | [T-02](T-02_simulated-backend/T-02_simulated-backend.md) | Simulated capture backend | epic | Done | PR-001, FR-15; closes when T-02.1 to T-02.5 are done | T-02.1 | 2026-11-10 |
| 9 | [T-03.3](T-03_startup-configuration/T-03.3_deployment-side.md) | The matching change in `deployment` | decision | Done | Q02-4 (Q01-4); stops T-03.1 and T-06.1 | — | 2026-11-09 |
| 10 | [T-03.1](T-03_startup-configuration/T-03.1_load-dotenv.md) | Load `.env` at start | code | Done | needs T-03.3 and T-03.2; the `deployment` part is T-06.1, done in the same piece of work | T-03.3, T-03.2 | 2026-11-10 |
| 11 | [T-03](T-03_startup-configuration/T-03_startup-configuration.md) | Start-up configuration | epic | Done | PR-002, FR-16; closes when T-03.1 to T-03.3 and T-06.1 are done | — | 2026-11-10 |

## C. Deployment tool changes (T-06, the `deployment` repository)

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 12 | [T-06.1](T-06_deployment-tool-changes/T-06.1_dotenv-in-the-catalogue.md) | `dotenv = true` and the tests that name the microphone | code | Done | lands with T-03.1 (F8) | T-03.1 | 2026-11-10 |
| 13 | [T-06.2](T-06_deployment-tool-changes/T-06.2_sim-preset.md) | The `sim` preset in the catalogue | code | Done | needs the answer of Q02-1 and the backend (T-02.3) | T-02.3 | 2026-11-10 |
| 14 | [T-06.3](T-06_deployment-tool-changes/T-06.3_readiness-without-a-device.md) | Readiness on a machine without a device | code | Done | `deploy` passes on `sim`, still fails on `real` without a device | T-06.2 | 2026-11-10 |
| 15 | [T-06.4](T-06_deployment-tool-changes/T-06.4_docker-on-windows-with-sim.md) | Docker on Windows for a microphone on `sim` | code | Done | Q02-6; without it the Docker acceptance is run by hand | T-06.2 | 2026-11-10 |
| 16 | [T-06.5](T-06_deployment-tool-changes/T-06.5_inventory-and-manual.md) | Inventory and manual | docs | Done | `env_inventory.py --write`, `DEPLOYMENT.md`, `deployment/CLAUDE.md` | T-06.1, T-06.2 | 2026-11-10 |
| 17 | [T-06](T-06_deployment-tool-changes/T-06_deployment-tool-changes.md) | Deployment tool changes | epic | Done | closes when T-06.1 to T-06.5 are done and the deployment suite passes | T-03.3, T-02.1 | 2026-11-10 |

## D. Docker and arm64 acceptance (T-07)

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 18 | [T-07.1](T-07_docker-and-arm64-acceptance/T-07.1_amd64-build.md) | Build the image on amd64 | manual | Done | Docker only with `sim` (F12) | T-06.2, T-03.2 | 2026-11-10 |
| 19 | [T-07.2](T-07_docker-and-arm64-acceptance/T-07.2_run-and-call.md) | Run the container on `sim` and call every endpoint | manual | Done | | T-07.1 | 2026-11-10 |
| 20 | [T-07.3](T-07_docker-and-arm64-acceptance/T-07.3_restart-recreate-stop.md) | Restart, recreate and `docker stop` | manual | Done | | T-07.2 | 2026-11-10 |
| 21 | [T-07.4](T-07_docker-and-arm64-acceptance/T-07.4_image-contents-and-secrets.md) | Image contents and secrets | manual | Done | | T-07.1 | 2026-11-10 |
| 22 | [T-07.5](T-07_docker-and-arm64-acceptance/T-07.5_docker-on-arm64.md) | Docker on arm64 | manual | Postponed | needs the Pi; postponed until Windows is 100 % | T-07.3 | 2026-11-09 |
| 23 | [T-07.6](T-07_docker-and-arm64-acceptance/T-07.6_record-the-results.md) | Record what was verified | docs | Done | | T-07.2, T-07.3, T-07.4 | 2026-11-10 |
| 24 | [T-07](T-07_docker-and-arm64-acceptance/T-07_docker-and-arm64-acceptance.md) | Docker and arm64 acceptance | epic | Done | closes when T-07.1 to T-07.4 and T-07.6 are done; T-07.5 stays postponed | T-06 | 2026-11-10 |

## E. Needs the maintainer and a microphone

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 25 | [T-04.1](T-04_hardware-verification/T-04.1_end-to-end-run.md) | Run `tests/simple.py` on a real microphone | manual | Done | *needs the maintainer* at the PC (Q01-8, Q02-9) | — | 2026-11-10 |
| 26 | [T-04.2](T-04_hardware-verification/T-04.2_tune-the-defaults.md) | Tune the treatment defaults | decision + code | Done | needs T-04.1; starts from the finding of 2026-11-09 (smoothing merges phrases about 5 s apart) | T-04.1 | 2026-11-10 |
| 27 | [T-04.3](T-04_hardware-verification/T-04.3_linux-and-raspberry-pi.md) | Linux and Raspberry Pi | manual | Postponed | until the services work at 100 % on Windows | — | 2026-11-09 |
| 28 | [T-04.4](T-04_hardware-verification/T-04.4_docker-dev-snd.md) | Docker with `/dev/snd` | manual | Postponed | Linux host work | T-04.3 | 2026-11-09 |
| 29 | [T-04](T-04_hardware-verification/T-04_hardware-verification.md) | Hardware verification | epic | Done | closes when T-04.1 and T-04.2 are done (T-04.3 and T-04.4 stay postponed) | T-01 | 2026-11-10 |

## F. Recurring

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 30 | [T-05](T-05_documentation-sync.md) | Documentation sync | docs | Recurring | first pass 2026-11-05 | the task being documented | 2026-11-05 |
