# T-04 — Hardware verification

| | |
|---|---|
| Status | done |
| Kind | epic |
| Depends on | T-01 |
| Blocks | — |
| Record | risks 1 and 9 of `docs/setup/14_risks-and-debt.md`; requirement notes "hardware pending" in `docs/requirements/requirements.md` |

## Goal

Find out how the service behaves on a real microphone, on Linux / Raspberry Pi and in Docker, which nothing in this repository has shown since the utterance cutting moved here (2026-10-05). The unit tests use a fake driver; the end-to-end suite of `contracts` uses fake hardware.

## Rules for the whole epic

- **The assistant cannot do these tasks alone.** It prepares the steps, the maintainer runs them at the machine and reports what happened; the assistant then records it. Never claim in a document that a hardware behaviour works unless the maintainer reported it.
- Ask before moving anything physical; this service has no motors, but the same rule of the workspace applies to any real device.
- Record results in each task's *Results* section with the date, the machine (OS, device name) and what was said or tried. No recordings, no device serial numbers.
- When a result changes a default or a rule, it goes through the normal path: a decision, an ADR (or a dated update of ADR-003), the requirement, the documents of the table in `CLAUDE.md`.

## Order

T-04.1 (a real microphone on Windows) -> T-04.2 (tune the defaults with what T-04.1 shows). **T-04.3 (Linux / Raspberry Pi) -> T-04.4 (Docker with `/dev/snd`) are `postponed`** (decision of the maintainer, 2026-11-09: the Pi and native Linux wait until the services work at 100 % on Windows).

## Exit criteria

- `tests/simple.py` was run on a real microphone and its outcome recorded; the treatment defaults are either confirmed or changed with a decision.
- The behaviour on Linux and in Docker is recorded, including what does not work.
- Every "hardware pending" in the documents is replaced by what was observed, with its date, or kept with the reason.

## Update 2026-11-09 (plan revision 2)

Exit criteria now: `tests/simple.py` was run on a real microphone and the defaults are confirmed or changed with a decision (T-04.1, T-04.2); the Linux and Docker-with-`/dev/snd` parts are postponed and are **not** exit criteria of this epic until the maintainer lifts the postponement. Audio tasks are run with the maintainer at the PC: the assistant says before the microphone opens and deletes every recording of the maintainer's voice at the end.
