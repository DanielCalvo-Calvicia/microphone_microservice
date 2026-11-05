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
| Recurring | Repeated after every change that touches the documents |

Written on 2026-11-05. **Todo (next)** is the task to start now. Tasks marked *needs the maintainer* cannot be completed by the assistant alone.

## A. Done: capture and utterances (T-01), history

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 1 | [T-01](T-01_capture-and-utterances/T-01_capture-and-utterances.md) | Capture and utterances | epic | Done | built 2026-09-20 to 2026-10-05; behaviour on a real microphone not re-checked since (T-04) | — | 2026-11-05 |

## B. Next

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 2 | [T-03.2](T-03_startup-configuration/T-03.2_requirements-split.md) | Split the requirements, lower bounds | code | **Todo (next)** | no decision needed; no other repository | — | 2026-11-05 |
| 3 | [T-02.1](T-02_simulated-backend/T-02.1_decisions.md) | Decisions: default, variable, signal | decision | **Awaiting user** | Q01-1, Q01-2, Q01-3; stops T-02.2 to T-02.5 | — | 2026-11-05 |
| 4 | [T-02.2](T-02_simulated-backend/T-02.2_sim-capture-adapter.md) | The simulated capture adapter | code | Blocked | needs T-02.1 | T-02.1 | 2026-11-05 |
| 5 | [T-02.3](T-02_simulated-backend/T-02.3_wiring-and-config.md) | Wiring and configuration | code | Blocked | needs T-02.2 | T-02.2 | 2026-11-05 |
| 6 | [T-02.4](T-02_simulated-backend/T-02.4_tests.md) | Tests of the backend | code | Blocked | needs T-02.3 | T-02.3 | 2026-11-05 |
| 7 | [T-02.5](T-02_simulated-backend/T-02.5_deployment-and-pipeline.md) | Deployment preset and pipeline check | code (other repository) | Blocked | needs T-02.4; touches `deployment` | T-02.4 | 2026-11-05 |
| 8 | [T-02](T-02_simulated-backend/T-02_simulated-backend.md) | Simulated capture backend | epic | Todo | PR-001, FR-15; closes when T-02.1 to T-02.5 are done | T-02.1 | 2026-11-05 |
| 9 | [T-03.3](T-03_startup-configuration/T-03.3_deployment-side.md) | The matching change in `deployment` | decision | **Awaiting user** | Q01-4; stops T-03.1 | — | 2026-11-05 |
| 10 | [T-03.1](T-03_startup-configuration/T-03.1_load-dotenv.md) | Load `.env` at start | code | Blocked | needs T-03.3 (the test of `deployment` must change in the same step) | T-03.3 | 2026-11-05 |
| 11 | [T-03](T-03_startup-configuration/T-03_startup-configuration.md) | Start-up configuration | epic | Todo | PR-002, FR-16; closes when T-03.1 to T-03.3 are done | — | 2026-11-05 |

## C. Needs the maintainer and a microphone

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 12 | [T-04.1](T-04_hardware-verification/T-04.1_end-to-end-run.md) | Run `tests/simple.py` on a real microphone | manual | Todo | *needs the maintainer* (Q01-8) | — | 2026-11-05 |
| 13 | [T-04.2](T-04_hardware-verification/T-04.2_tune-the-defaults.md) | Tune the treatment defaults | decision + code | Blocked | needs T-04.1 | T-04.1 | 2026-11-05 |
| 14 | [T-04.3](T-04_hardware-verification/T-04.3_linux-and-raspberry-pi.md) | Linux and Raspberry Pi | manual | Todo | *needs the maintainer* and a Linux machine | — | 2026-11-05 |
| 15 | [T-04.4](T-04_hardware-verification/T-04.4_docker-dev-snd.md) | Docker with `/dev/snd` | manual | Blocked | needs T-04.3 | T-04.3 | 2026-11-05 |
| 16 | [T-04](T-04_hardware-verification/T-04_hardware-verification.md) | Hardware verification | epic | Todo | closes when T-04.1 to T-04.4 are done | — | 2026-11-05 |

## D. Recurring

| # | Task | Name | Kind | State | Detail | Depends on | Last updated |
|---|---|---|---|---|---|---|---|
| 17 | [T-05](T-05_documentation-sync.md) | Documentation sync | docs | Recurring | first pass 2026-11-05 | the task being documented | 2026-11-05 |
