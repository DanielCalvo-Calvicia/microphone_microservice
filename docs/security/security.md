# Security

Only what can be verified in the repository. Labels: **Implemented** (in the code and tested), **Required** (the person who deploys must do it), **Not implemented**, **Recommended but not implemented**.

## Access and authentication

- **Not implemented:** authentication or authorisation. Every caller that reaches the port can start, stop and read the microphone. Service-to-service authentication is not designed for the project yet (the one speaker had was removed, see `../CLAUDE.md`). There is no CORS configuration and no rate limit. The `MICROPHONE_API_KEY` and `APP_ENV` that old notes mention are read by no code (checked by search; the `.env*` files themselves were not opened).
- **Required:** keep the port reachable only from the machine that runs Brain. The default bind is `127.0.0.1`; setting `SERVICE_HOST=0.0.0.0` (needed when Brain is on another machine) exposes the live microphone to the whole network segment, so restrict it with the firewall of the host (Windows Firewall rule, `ufw`, a Docker network).
- **Recommended but not implemented:** a shared token between Brain and the service once the project designs it.

## Privacy of what is captured

- **Implemented:** the audio is only held in memory and sent on the stream; no file is written and no sample or base64 audio is logged (`docs/operations/monitoring.md`).
- **Implemented:** the device is released when the stream ends, when the client disconnects, on `/stop` and on shutdown, so the microphone is not left open (unit tests with a fake driver; hardware not re-checked).
- **Required:** the operating system's microphone permission must be allowed for desktop apps (Windows: Settings, Privacy & security, Microphone). Anyone who can call `GET /stream` after a `POST /start` hears the room.

## Input handling

- **Implemented:** the body of `/start` is validated (FastAPI types, then `AudioFormat` rejects values of 0 or less with `422`); a `sample_rate` that contradicts the capture is refused; the error detail returned to the caller is the error text (device names can appear in it).
- **Implemented:** the treatments are validated at start-up (`InputTreatment`), so a bad value stops the service instead of producing wrong audio.

## Secrets and files

- No secret belongs to this service: none of its variables is sensitive (`docs/configuration/environment-variables.md`).
- **Required:** `.env`, `.env.staging` and `.env.production` are git-ignored (`.env*` with `!.env.example`); never commit or copy them, and put no secret value in `.env.example`, tests or documents.

## Supply chain

- **Supply chain:** since 2026-11-09 (T-03.2) the runtime requirements pin the four packages the service imports to exact versions, the bundled `contracts` wheel is named by version, and the development tools are in `requirements-dev.txt`, which the deploy tool never installs. **Not locked:** the packages those depend on (no lock file). See `docs/proposals/PR-002-dotenv-and-requirements-split.md`.
- **Implemented:** `contracts` comes from a wheel bundled in `vendor/`, refreshed by `contracts/scripts/bundle.py`, never edited by hand.

- **A simulated device is not a security feature (T-06.5):** `MICROPHONE_BACKEND=sim` generates a tone and opens no device, so it listens to nothing and captures nothing; it does not hide anything either, because `/available` says `simulated microphone` in its `reason` and the service logs a warning at start. The risk it adds is operational: the deploy catalogue presets `sim`, so a machine with a real microphone that forgets `MICROPHONE_BACKEND = "real"` in its `config/local/microphone.toml` is healthy and deaf.

- **Docker image (T-07.4, 2026-11-10):** the image holds no `.env` file and no secret (counts in `docs/deployment/deployment.md`); the `.env` is a read-only bind mount. The process runs as **root** (the generic Dockerfile sets no `USER`); the image also contains `tests/`, `docs/` and `.engram/` because it copies the whole service tree. Not fixed: both belong to the deployment tool's Dockerfile.
