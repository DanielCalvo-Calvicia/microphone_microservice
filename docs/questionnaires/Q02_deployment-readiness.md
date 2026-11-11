# Q02 — Before the deployment-readiness tasks (T-06, T-07 and the open decisions of T-02 and T-03)

**Answered by the maintainer on 2026-11-09: "Recommended" for all nine questions; processed into ADR-007, the Resolution of T-02.1, T-03.3 and T-06.4, PR-001 and PR-002.** (Original text follows.) Written on 2026-11-09 with the plan revision 2 of [../tasks/README.md](../tasks/README.md), after the deployment audit ([../deployment_audit/microphone.md](../deployment_audit/microphone.md)) was checked against the code. It **re-asks** Q01-1 to Q01-4 of [../setup/questionnaires/Q01_open-questions.md](../setup/questionnaires/Q01_open-questions.md) (still unanswered) with the facts found since, and adds what the deployment work needs. It lives here, beside the questionnaires of stt and tts, because it is about deployment; Q01 stays where it is and its remaining questions (5 to 10) are unchanged.

Write your answer after `A:` (English or Spanish); `[x]` marks a choice; `UNKNOWN`, `NOT APPLICABLE` and `LATER` are valid; **never write secrets**. Every question gives my **recommended** answer, so "Recommended" is a valid answer.

**Stops the chain:** 1, 2 and 3 stop T-02.1 (and so T-02.2 to T-02.5 and T-06.2, T-06.3, T-07.x); 4 stops T-03.3 (and so T-03.1 and T-06.1). 5 to 9 only change how later tasks are run.

---

1. **The switch (Q01-1 and Q01-2).** `MICROPHONE_BACKEND=real|sim`, **code default `real`** (a silent fake default would make a robot with a broken microphone look healthy), an unknown value stops the start naming the variable. Where a deployed machine has no microphone it starts on `sim` through a **catalogue preset** (`[services.microphone.env] MICROPHONE_BACKEND = "sim"`, like stepper's `MOCK_HARDWARE = "1"`), and the machine with the sound card sets `real` in `deployment/config/local/microphone.toml`.
   *Consequence to accept:* with that preset a **default** deploy of the microphone is `sim`; if you forget `real` on the robot, the service is healthy and silent. The tool's `healthy and available, warning: <reason>` line (question 2) is the safety net, and the manual will say it in the microphone row.
   - [ ] as recommended (default `real`, preset `sim` in the catalogue)
   - [ ] default `real` and **no** preset: a machine without a device sets `sim` in its own local file
   *Recommended: the first.*
   A:Recommended

2. **How the active backend is reported.** (a) In the `reason` of `GET /available` (what tts did, [tts ADR-008](../../../tts_microservice/docs/decisions/ADR-008-fallback-reported-in-available-reason.md): `is_available` stays true, `reason` is a short note, no `contracts` change; the deploy tool already prints `healthy and available, warning: <reason>`), for example `simulated microphone (MICROPHONE_BACKEND=sim)`; the real backend leaves `reason` empty. (b) A new `backend` field in `contracts` (a version bump that every service re-bundles).
   *Recommended: (a).* One caveat to know: Brain reads `reason` only when `is_available` is false, so Brain itself will not show it.
   A:Recommended

3. **What does the simulated microphone say (Q01-3), and how fast?** Seed: `SineStream` of `contracts/tests/e2e/fake_services.py` (5 chunks of room noise at amplitude 20, 80 chunks of a 300 Hz tone at 8000, then silence). Two points: (a) signal: a generated pattern, no file (recommended), or a looped WAV; (b) pacing: the real microphone delivers one chunk per `chunk_size / sample_rate` seconds, so the sim **sleeps that long per chunk** (real time, recommended: Brain's echo guard and the cutting see a realistic stream; `SineStream` sleeps 10 ms only because it is a test double), or runs as fast as the consumer reads. And the pattern: once per `/start` then silence (recommended), or repeated every N seconds so a robot on `sim` keeps "hearing" someone.
   *Recommended: generated pattern, real-time pacing, once per `/start`.*
   A:Recommended

4. **`python-dotenv` and `dotenv = true` (Q01-4).** Add `python-dotenv` and load the `.env` in `main_flow/http.py` as stt and stepper do, and in the **same piece of work** set `dotenv = true` in `deployment/config/catalogue.toml` and change `deployment/tests/test_env_file_only.py` (it asserts `dotenv is False` for the microphone at line 130, a Docker case at line 218 names it as the exception, and a third test, `test_the_dotenv_flag_of_every_service_matches_what_its_source_does`, fails the moment the service reads a `.env` while the flag is false), the manual (lines 292 and 315) and `deployment/CLAUDE.md`. Or keep `service_runner.py`.
   *Recommended: add it, both repositories in one piece of work (the deployment suite fails otherwise).*
   A:Recommended

5. **Docker on a Windows host for an audio service.** The tool rejects `runtime = "docker"` for an audio service on Windows (`deployment/domain/rules/host_validation.py:18`) because Docker cannot reach the Windows sound card. Keep the rejection and document it (and prove Docker here only with `sim`), or implement the per-machine `mode = "local"` override that the decision of 2026-11-04 named?
   *Recommended: keep the rejection and document it.* A Docker run on this PC is then possible only for a microphone on `sim`, where the tool's rule would still refuse it (it checks `audio`, not the backend): see question 6.
   A:Recommended

6. **Docker acceptance on this PC (amd64, Docker Desktop).** The rule above refuses a Docker microphone on Windows even on `sim`. Options: (a) the acceptance runs the image **by hand** (`docker build` with the tool's Dockerfile and `docker run` with `MICROPHONE_BACKEND=sim`, as the tests of T-02/T-03 of stt did with the tool for the rest), not through `oblivion.py`; (b) the rule is made smarter: a service whose backend is `sim` (read from its resolved env) may run in Docker on Windows, which is a small change in `host_validation.py` and a test, and lets `oblivion.py deploy` prove the whole chain.
   *Recommended: (b)* if you accept a small change in the tool; otherwise (a). In both cases the image and the container are proven only with the simulated backend; the real device is proven natively on Windows, and `/dev/snd` is Linux/Pi work (postponed).
   A:Recommended

7. **Requirement pins.** stt pinned the runtime packages to the exact versions that ran (`==`); tts left lower bounds (`>=`). Which for the microphone? Today's venv: fastapi 0.136.1, uvicorn 0.47.0, sounddevice 0.5.5, numpy 2.4.5 (the audit's convention was lower bounds).
   *Recommended: exact `==` of the versions that were installed and run (as stt), with the dev tools in `requirements-dev.txt`.* Also: the file names stay the ones T-03.2 names (`requirements-dev.windows.txt` and `requirements-dev.linux.txt`) or become the single `requirements-dev.txt` of tts, or `requirements.dev.txt` of stt?
   *Recommended: one `requirements-dev.txt`, as tts (the two platform files are identical).*
   A:Recommended

8. **The defaults after the pre-roll (T-04.2).** With the default smoothed volume phrases said about 5 s apart merge into one utterance (about 1.8 s for the smoothed volume to fall under the end threshold plus the 2 s silence limit); with smoothing off each phrase was its own utterance. Do you want the code defaults changed only **after** a real recording is re-cut offline and scored (recommended: it needs your voice and the room, task T-04.2), and meanwhile only your machine's `config/local/microphone.toml` changed? Or should smoothing go off by default now?
   *Recommended: no change to the code defaults until T-04.2 has numbers.*
   A:Recommended

9. **How the manual tasks run.** Tasks that open the microphone, play sound, build a Docker image or download something are `manual`. Same standing permission as stt/tts (Q01-12 there): you say "go" for **each** task, I say first what it does and costs, I warn before the microphone opens, you are at the PC for the audio ones, recordings of your voice and the scratch folders are deleted at the end, and ports 7998 to 8005 are checked free before and after. And the order: microphone first, then speaker, in one session (both edit `deployment/config/catalogue.toml` and `deployment/docs/DEPLOYMENT.md`).
   *Recommended: yes to both.*
   A:Recommended
