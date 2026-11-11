# 11 — Runtime and deployment

> Depends on: 05, 09, 10. The detail is [../deployment/deployment.md](../deployment/deployment.md).

| Field | Answer |
|---|---|
| Runtime form | A long-running HTTP service (uvicorn), one process, one capture at a time |
| Hosting | The machine that has the sound card: Windows PC, Linux server or Raspberry Pi; each service runs on exactly one machine, chosen in the deployment layout |
| Environments | `.env.staging` and `.env.production` exist next to `.env` (git-ignored, not opened); what they mean is UNKNOWN |
| Container | No `Dockerfile` in this repository; the deployment tool builds it. Linux host: `--device /dev/snd` is added because the catalogue has `audio = true`; Windows host: Docker cannot reach the sound card, so `runtime = "native"` |
| Health checks | `/health` (liveness) and `/available` (readiness, the device probe) |
| CI/CD | UNKNOWN in this repository (no workflows); deployment is `deployment/oblivion.py` (`deploy`, `update`, `rollback`) |
| Deployment / releases | The tool clones the `feature_ai_claude_2` branch, installs the requirements for the platform and the library `shared-logging`, then starts the service; `update` pulls and restarts, rolling back to the previous commit if the readiness check fails after a pull |
| Configuration | Environment variables; the tool reads the catalogue and `config/local/microphone.toml` and writes them into the `.env` the service loads (`dotenv = true`) |
| Secrets | None |
| Network | Bind `127.0.0.1:8000` by default; `SERVICE_HOST=0.0.0.0` when Brain is on another machine, with the firewall as the only protection |
| Start order | Independent of the other services; before Brain, which waits for `/available` of the microphone, STT, TTS and speaker |
| Linux / Raspberry Pi | `requirements.linux.txt`, `audio` group for a native run; not run on real hardware |
