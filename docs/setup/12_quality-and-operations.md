# 12 — Quality and operations

> Depends on: 10, 11

| Topic | Answer |
|---|---|
| Performance targets | UNKNOWN as numbers. The design goal is that an utterance reaches Brain right after the silence that ends it (`MICROPHONE_SILENCE_LIMIT_SECONDS`, default 2.0 s), and that reading the device never blocks the event loop |
| Availability | UNKNOWN; a restart returns to idle and Brain must call `/start` again |
| Authentication / authorization | None (ADR-005) |
| Who triggers a capture | Brain, by `POST /start` |
| Logging | `shared_logging`, constant messages with fields, one request line per request, trace id on every record; never audio (`docs/operations/monitoring.md`) |
| Monitoring / alerting | None; `Stream closed` logs chunks, bytes and overflows |
| Error-handling convention | Domain and application errors, mapped to HTTP only in `http_error_mapper.py`; sounddevice errors wrapped by `sounddevice_error_mapper.py` |
| Testing strategy | pytest: `tests/domain`, `application`, `infrastructure`, `composition_root`, `architecture`, with a fake `AudioDriver`; `tests/simple.py` end to end on a real microphone; the workspace suite `contracts/tests` starts the real service with fake hardware. Result 2026-11-10: 171 passed in 2.3 s (127 on 2026-11-05, 142 on 2026-11-09) |
| Linter / formatter | ruff (clean), mypy strict (clean, 56 files); black is configured and was not run |
| Documentation | `docs/{architecture,api,configuration,operations,requirements,security,deployment,decisions,proposals,setup,tasks}`; the rule that keeps them true is in `CLAUDE.md` |
| Branching / review | Work on `feature_ai_claude_2`; the maintainer commits and pushes when asked |
| On-call / support | None |
