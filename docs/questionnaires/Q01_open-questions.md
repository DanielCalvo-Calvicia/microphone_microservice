# Q01 — Open questions after the documentation pass of 2026-11-05

**Awaiting the maintainer; nothing is answered yet.** These are the points that the code, the git history and the deployment audit do not settle. Each gives my **recommended** answer; none of them is built or changed until you answer. Same format as the other projects: write after `A:`; `UNKNOWN`, `NOT APPLICABLE` and `LATER` are valid; never write secrets.

Blocking: questions 1 to 3 stop task T-02.1, and question 4 stops T-03.3 (see [../tasks/ORDER.md](../tasks/ORDER.md)).

---

1. **Where does the simulated backend start by default?** The proposal (PR-001) keeps the **code default `real`**, so a robot with a broken microphone never looks healthy, and sets `sim` only where a deployed machine asks for it (a preset in the catalogue, as stepper does with `MOCK_HARDWARE`, and `real` in `config/local/microphone.toml` on the machine with the sound card). The alternative is `sim` as the code default, which makes a fresh checkout run anywhere but can hide a missing microphone.
   *Recommended: code default `real`.*
   A:

2. **What is the variable?** Proposed: `MICROPHONE_BACKEND=real|sim` (an unknown value stops the start). Alternative: a boolean like stepper's `MOCK_HARDWARE`, which keeps the workspace consistent but allows only two backends.
   *Recommended: `MICROPHONE_BACKEND`.*
   A:

3. **What does the simulated microphone say?** Seed: `SineStream` in `contracts/tests/e2e/fake_services.py` (room noise, a tone, silence), which exercises the utterance cutting. Alternative: a looped WAV file, which lets you replay a real sentence but needs a file path setting and a file in the repository or on the machine.
   *Recommended: the generated signal, with a fixed pattern (noise, tone for a configurable time, silence), no file.*
   A:

4. **May the `.env` loading change `deployment`?** Loading `.env` in `main_flow/http.py` (as stt and stepper do) means setting `dotenv = true` in `deployment/config/catalogue.toml`, changing `deployment/tests/test_env_file_only.py` (it asserts `dotenv is False` for the microphone) and two lines of `deployment/docs/DEPLOYMENT.md`. That is another repository. Do you want it done in the same piece of work, or only the microphone side now?
   *Recommended: both, in the same piece of work, because a test of `deployment` fails otherwise.*
   A:

5. **Should `MICROPHONE_SHOW_METER` default to `false`?** Today it is `true` and writes a rewritten line to stdout on every chunk, which is noise in a service log. Changing the default changes behaviour for anyone who relies on seeing the meter.
   *Recommended: `false`, and say so in the README; turn it on for a manual test.*
   A:

6. **May the stale `.engram/` folder and `docs/old/` be removed?** `.engram/` holds five short notes of the first refactor (one of them, D6, is about a `MICROPHONE_API_KEY` that no code reads); `docs/old/` holds the pre-refactor design (1,527 lines). They are marked stale in `CLAUDE.md`; git keeps their history.
   *Recommended: remove both in a separate commit.*
   A:

7. **What are `.env.staging` and `.env.production` for?** They sit next to `.env`, are git-ignored and were not opened. Does anything use them (the deployment tool does not read them, as far as its manual says), and do they still list `MICROPHONE_API_KEY` or `APP_ENV`?
   *Recommended: if nothing uses them, delete them yourself; I will not open them.*
   A:

8. **When can the hardware session happen?** T-04 needs you at the machine with the microphone: run `tests\simple.py`, say a few sentences at the default thresholds, and report what is clipped or never ends. I cannot do this part.
   *Recommended: before building PR-001, so the defaults are known good.*
   A:

9. **Contact and repository visibility.** File 01 of the setup says UNKNOWN for both. Do you want a contact and the visibility written in the documents? (Not needed to work.)
   *Recommended: `LATER`.*
   A:

10. **Commit message convention.** The history uses short imperative subjects. Do you want that written down as the rule, with the `Co-Authored-By` line the tool adds?
    *Recommended: yes, as it is.*
    A:
