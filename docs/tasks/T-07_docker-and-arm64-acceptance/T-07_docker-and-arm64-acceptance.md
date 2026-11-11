# T-07 — Docker and arm64 acceptance

| | |
|---|---|
| Status | done |
| Kind | epic |
| Depends on | T-02, T-03.2, T-06 |
| Blocks | — |

## Goal

Prove, by running it on this PC (amd64, Docker Desktop, F12), that the microphone image builds, runs and answers every endpoint, survives a restart and a recreate, holds no secret and no dev tools, and stops cleanly with `docker stop`. **Only with the simulated backend**: Docker on a Windows host cannot reach the sound card. The real device is proven natively on Windows (T-04); a container with `/dev/snd` is Linux/Pi work and is postponed (T-04.4, T-07.5).

## Rules for the whole epic

- Never deploy from the working folders and never touch `deployment/config/local`. Copy the working tree of the microphone (without `windows/`, `.git`, `.env*`, caches) into a scratch folder, `git init` and commit it there, write a scratch config folder (the catalogue with absolute library paths, `services/`, a one-machine layout, `robot.toml`, `machines/robot.toml` with a scratch workdir, `local/microphone.toml` with `git = "<scratch repo>"` and `MICROPHONE_BACKEND = "sim"`) and run `oblivion.py <command> --host robot --config <scratch config>`; stt's [T-03.1](../../../../stt_microservice/docs/tasks/T-03_docker-and-arm64-acceptance/T-03.1_amd64-build.md) describes it. If the tool refuses Docker for an audio service on Windows and Q02-6 is not yet built, use the manual route: `docker build` with the tool's Dockerfile and `docker run` with the same flags the tool prints in `--dry-run`.
- Always `docker --context desktop-linux ...`; set `MSYS_NO_PATHCONV=1` in Git Bash; remove only the containers, images and volumes this run created; delete the scratch folders at the end.
- Each task is `manual`: say what it does and costs, wait for "go" (Q02-9). Ports 7998 to 8005 are free before and after.
- No audio device is used and no sound is recorded or played in this epic.

## Subtasks

| Order | Task | Kind | State |
|---|---|---|---|
| 1 | [T-07.1 Build the image on amd64](T-07.1_amd64-build.md) | manual | blocked |
| 2 | [T-07.2 Run the container on `sim` and call every endpoint](T-07.2_run-and-call.md) | manual | blocked |
| 3 | [T-07.3 Restart, recreate and `docker stop`](T-07.3_restart-recreate-stop.md) | manual | blocked |
| 4 | [T-07.4 Image contents and secrets](T-07.4_image-contents-and-secrets.md) | manual | blocked |
| 5 | [T-07.5 Docker on arm64](T-07.5_docker-on-arm64.md) | manual | postponed |
| 6 | [T-07.6 Record what was verified](T-07.6_record-the-results.md) | docs | blocked |

## Exit criteria

T-07.1 to T-07.4 and T-07.6 are done with the numbers recorded; the documents say which routes were proven (Docker with `sim` on amd64) and which were not (`/dev/snd`, arm64, a real device in a container).
