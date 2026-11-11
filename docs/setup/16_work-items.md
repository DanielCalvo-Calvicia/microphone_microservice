# 16 — Work items

> Depends on: 15. The real plan is `docs/tasks` ([ORDER.md](../tasks/ORDER.md)).

## Template (one per item)

```
### SPEC ID: mic-XXX
Title:
Type: feature | bugfix | techdebt | migration
Priority: high | medium | low
Blocked by: (spec ids / open questions)

PROPOSAL
- Problem:
- Proposed solution:
- Out of scope:
- Affected layers/paths:

TASKS
- [ ] 1.

EXPECTED RESULTS
- Acceptance criteria (testable):
- Verification (commands / tests):
```

## Epics

| ID | Title | Type | State |
|---|---|---|---|
| `mic-001` | T-01 capture and utterances: the layered service, the contract stream, the utterance cutting and its treatments (history, built between 2026-09-20 and 2026-10-05) | feature | done (hardware pending, see `mic-003`) |
| `mic-002` | T-02 simulated capture backend (PR-001): a `sim` backend behind the same ports so a machine without a microphone can run and be deployed | feature | built 2026-11-10 (T-02.1 to T-02.4); T-02.5 (pipeline check) todo |
| `mic-003` | (T-04.1 done 2026-11-10) T-04 hardware verification: run `tests/simple.py`, tune the defaults on real rooms, Linux / Raspberry Pi, Docker with `/dev/snd` | techdebt | todo; needs the maintainer and a microphone |
| `mic-004` | T-03 start-up configuration (PR-002): load `.env`, split the requirements, lower bounds, the matching change in `deployment` | techdebt | todo; T-03.3 is `awaiting-user` (Q01-4) |
| `mic-005` | T-05 documentation sync | techdebt | recurring; the first pass was done on 2026-11-05 |

Full detail of each epic, with its leaf tasks, files and acceptance criteria, is in the task files.
