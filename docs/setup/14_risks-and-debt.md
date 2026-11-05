# 14 — Risks and debt

> Depends on: 10–13

| # | Item | Kind | Impact | Mitigation / next step |
|---|---|---|---|---|
| 1 | The sounddevice adapter and the cutting thresholds are not validated on real hardware since 2026-10-05 | Risk | Clipped starts, endless utterances in a noisy room, or no speech detected; unknown until tested | T-04 (hardware verification; needs the maintainer and a microphone) |
| 2 | No simulated backend: a machine without a microphone is `is_available: false`, Brain's preflight requires it and the deployment readiness check reports a failed deploy (an `update` then rolls back a healthy commit) | Debt | The pipeline cannot run on a machine without a microphone | PR-001, T-02 |
| 3 | The service does not load `.env`; the catalogue has `dotenv = false` and the deployment tool has a special path | Debt | A hand start must export the variables; a quirk in the Docker env path | PR-002, T-03 |
| 4 | Dev tools in the runtime requirements and nothing pinned | Debt | Heavier installs; an upstream change can break a deploy | PR-002, T-03 |
| 5 | No authentication, no CORS, no rate limit; with `SERVICE_HOST=0.0.0.0` anyone on the network can start the capture and hear the room | Risk | Privacy | Firewall of the host now (`docs/security/security.md`); a project-wide design later (ADR-005) |
| 6 | The utterance in progress is lost if the device fails mid-stream | Limit | One phrase is lost | Accepted (ADR-003); revisit if it happens in practice |
| 7 | `channels > 1` is mixed to mono silently and the answer says `channels = 1` | Limit | A caller that asks for stereo is not told | Accepted; documented in the API |
| 8 | The resample is linear interpolation, not a filtered converter | Limit | Some aliasing when downsampling 48 kHz to 16 kHz | Accepted; revisit if STT accuracy suffers |
| 9 | Docker on Linux: the image has no ALSA configuration, so "the OS default input" may find no device in a container | Risk | A container that cannot hear | T-04 (needs a Linux host with a sound card) |
| 10 | The console meter is on by default and writes to stdout on every chunk | Debt | Noise in service logs | Set `MICROPHONE_SHOW_METER=false` outside manual tests; changing the default is a decision (Q01-5) |
| 11 | The `.engram/` folder and `docs/old/` are stale and contradict the code | Debt | Misleading to a reader | Marked stale in `CLAUDE.md` and the docs index; removal needs the maintainer (Q01-6) |
| 12 | `.env`, `.env.staging`, `.env.production` exist and were not opened; what the staging and production files are for is unknown | Unknown | Possible variables the code does not read | Ask the maintainer (Q01-7) |
