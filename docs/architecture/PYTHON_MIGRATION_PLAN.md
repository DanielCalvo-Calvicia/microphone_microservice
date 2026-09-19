# Migration Plan — `microphone_microservice` → Engram Architecture Standard (Python edition)

This document explains how to change the **current** project so it satisfies the Engram architecture standard (`ENGRAM_ARCHITECTURE_PROMPT.md`, written for Go), adapted to Python. It covers two things: **how the folder structure must change** and **how the code inside it must be reorganized**.

It is a plan, not an executed change. Nothing in the repository has been modified.

---

## 0. Starting point (read this first)

The working tree is already halfway there. The only git commit (`init`) still contains the old design (DTO + mapper layers, `AdapterInboundPort`/`AdapterOutboundPort`, `FastApiAdapter`, ~150 `print` calls). The **uncommitted** working tree contains a first Clean-Architecture refactor:

- `domain/` exists (`entities`, `value_objects`, `operations`, `errors.py`), depends on nothing but the stdlib.
- `application/` has ports, one DTO, one service, and no framework imports.
- `tests/architecture/test_dependency_rules.py` already enforces dependency direction by parsing imports.
- `print` was replaced with `logging`.

So this plan is a **second pass**: it aligns that refactor with the standard's naming, folder layout, error ownership, config handling and entry-point contract. **Commit the current working tree first** (`git add -A && git commit -m "refactor: clean architecture first pass"`) so this migration is a reviewable diff on top of it and not mixed with the first pass.

`docs/general.md` and `README.md` still describe the *old* design (mappers, `InitInboundAdapterDto`, `start_autoload`/`stop_autoload`, `FastApiAdapter`, `get_app`, `{service}-contracts` packaging). They contradict the standard and must be retired (Phase 7).

---

## 1. How the Go standard translates to Python

The rule the user set: the Python version is *very* similar to Go; the only structural differences are that **`internal/` and `pkg/` do not exist** and their contents sit directly at the repository root.

| Go standard | Python edition |
|---|---|
| `internal/domain/`, `internal/application/`, `internal/infrastructure/`, `internal/composition_root/` | `domain/`, `application/`, `infrastructure/`, `composition_root/` **at the repo root** |
| `pkg/` (external-consumer code) | **Does not exist.** Nothing is published. The old `{service}-contracts` packaging guidance is dropped. |
| `cmd/main.go` + `cmd/main_flow/<entry>.go` | `main.py` + `main_flow/<entry>.py` at the root (see decision D1: the name `cmd` is not usable in Python) |
| `go.mod` | `requirements.<platform>.txt` + `pyproject.toml` (tool configuration only) |
| `snake_case.go`, lowercase package names | `snake_case.py`, lowercase package names, `PascalCase` classes |
| Sentinel errors + `JoinErrors` (`errors.Join`) | Exception classes per layer + `raise NewError(...) from cause` (keeps the root cause) |
| `var _ Port = (*Impl)(nil)` compile-time check | Subclassing the `ABC` port (instantiation fails if abstract methods are missing) + `mypy` |
| `context.Context` first parameter | Not applicable |
| `envconfig` struct tags | Frozen dataclass in `infrastructure/config/` with explicit env-var names |
| `go test ./... / go vet / gofmt` | `pytest` / `mypy` / `ruff check` + `black --check` |

Everything else carries over unchanged: dependency direction `infrastructure → application → domain`; domain has no I/O; application owns the ports; outbound adapters implement outbound ports; inbound adapters call inbound ports and hold no business rules; the composition root is the only place concrete adapters are constructed; no `utils` / `common` / `helpers` packages.

Severity tags below (`[MANDATORY]`, `[DEFAULT]`, `[OPTIONAL]`) keep the standard's meaning. The anti-over-engineering principle applies: where a DEFAULT pattern would add abstraction without solving a real problem, this plan says so and skips it.

---

## 2. Gap analysis

| # | Area | Current state | Standard says | Severity |
|---|---|---|---|---|
| G1 | Entry point | `main.py` calls `composition_root/setup/setup.py`, which also reads env, configures logging and runs uvicorn | Entry orchestration lives outside the composition root (`main_flow`); composition root only has `containers/` and `dependencies/` | MANDATORY (bootstrapping ≠ business/wiring) |
| G2 | Config | `HOST`, `PORT`, `NAME` constants in `setup.py`; `LOG_LEVEL` read inline; fallback rate / keywords / meter hardcoded in `container.py`; `APP_ENV` and `MICROPHONE_API_KEY` defined but never read; no `.env.example` | Typed config per bounded concern in `infrastructure/config/`; every env var documented in `.env.example`; no secret defaults | DEFAULT |
| G3 | Error ownership | Service raises bare `RuntimeError("Failed to stop…")`; port docstring says "raises an exception"; sounddevice/PortAudio errors can reach the service untranslated | Outbound adapters translate driver errors into application/domain errors at the port boundary; application has its own `errors.py` | MANDATORY (adapter never returns raw SDK errors) |
| G4 | Port layout | `application/ports/service_port.py` and `microphone_port.py` side by side; names do not say which is inbound/outbound; `ServicePort` imports `AudioStream` from the *outbound* port module | `ports/inbound/` and `ports/outbound/`; one interface per file, named `<Concept>Port` | DEFAULT |
| G5 | DTO naming | `stream_dtos.py` with `StartStreamCommand` | `<dto>_inbound.py` / `<dto>_outbound.py`, one plain data holder per file | DEFAULT |
| G6 | Inbound adapter | `routes/microphone_routes.py`: a `build_microphone_router(service)` closure plus module-level helpers | One handler class constructed with the inbound port; error translation in `<protocol>_error_mapper.py` | DEFAULT |
| G7 | Outbound adapter | `outbound/sounddevice_microphone.py` (208 lines, two classes, no error translation) | `outbound/<adapter_name>/…`, split by responsibility, separate error mapper | DEFAULT |
| G8 | Composition root | One `generate_microphone_dependency()` builds adapter, service, FastAPI app and router; container is called `Container` / `BuildContainer` | Factories in `dependencies/`, one declarative container per initialization configuration; snake_case function names | DEFAULT |
| G9 | Tests | No composition-root wiring test; `tests/simple.py` builds the container directly | A wiring smoke test per container; e2e stays available | DEFAULT |
| G10 | Tooling | No `pyproject.toml`, no ruff/black/mypy config, no `__init__.py` files; `httpx` (used by tests) missing from requirements; unused `soundfile` present | Verification commands must be runnable | DEFAULT |
| G11 | Docs / repo hygiene | `docs/general.md` and `README.md` describe a deleted design; `.env*` fully git-ignored so no `.env.example` can be committed; `windows/` venv, `.tmp_pydeps.tar`, stale `__pycache__` directories inside the repo; no `.engram/` | Historical docs move to `docs/old/`; `.engram/` project files exist | DEFAULT |

What is **already compliant** and must not be touched: the `domain/` package and its rules, `MicrophoneService` being constructor-injected with a port, the import-direction architecture test, `pytest.ini`, and the domain / application / infrastructure test folders.

---

## 3. Target structure

```text
microphone_microservice/
├── main.py                                   # calls exactly one main_flow function
├── main_flow/                                # entry-point orchestration only (no business logic)
│   ├── http.py                               # config → container → uvicorn → graceful shutdown
│   └── logging_setup.py
├── domain/                                   # unchanged
│   ├── entities/microphone.py
│   ├── value_objects/audio_format.py
│   ├── operations/{pcm.py, format_negotiation.py}
│   ├── errors.py
│   └── rules.py                              # [OPTIONAL] e.g. SAMPLE_WIDTH_BYTES, moved out of operations/pcm.py
├── application/
│   ├── dtos/
│   │   ├── start_stream_inbound.py           # StartStreamInboundDTO
│   │   └── stream_outbound.py                # StreamOutboundDTO
│   ├── ports/
│   │   ├── inbound/microphone_streaming_port.py
│   │   └── outbound/
│   │       ├── audio_capture_port.py
│   │       └── audio_stream_port.py
│   ├── services/microphone_service.py
│   └── errors.py                             # ApplicationError, MicrophoneUnavailable, StreamCloseFailed
├── infrastructure/
│   ├── inbound/http/
│   │   ├── http_handler.py                   # MicrophoneHandler (routes + request/response models)
│   │   ├── http_error_mapper.py
│   │   └── http_envelope.py                  # success/failure JSON envelope builders
│   ├── outbound/sounddevice_capture/
│   │   ├── sounddevice_audio_capture.py      # implements AudioCapturePort
│   │   ├── sounddevice_audio_stream.py       # implements AudioStreamPort
│   │   └── sounddevice_error_mapper.py
│   └── config/
│       ├── server_config.py
│       └── microphone_config.py
├── composition_root/                         # the only place concrete adapters are imported together
│   ├── containers/http_container.py
│   └── dependencies/microphone_dependencies.py
├── tests/
│   ├── domain/  application/  infrastructure/  composition_root/  architecture/
│   └── simple.py                             # e2e (needs a real microphone)
├── docs/{architecture/, old/, tasks/, requirements/, rules/}
├── .engram/{project.md, architecture.md, constraints.md, decisions.md, overrides.md, specs/}
├── .env  .env.staging  .env.production  .env.example
├── pyproject.toml
├── pytest.ini
├── requirements.windows.txt
└── README.md
```

Folders from the Go tree that are intentionally **omitted** (record in `.engram/project.md`, they are not violations): `.devcontainer/`, `.github/`, `k8s/`, `Dockerfile`, `docker-compose.yml`, `.goreleaser.yml`, `pkg/`, `domain/base_value_objects/`. Add them only when the project really needs them (this service drives local audio hardware on Windows).

`domain/base_value_objects/` is omitted on purpose: `AudioFormat` is a standalone value object (Shape A). Extract a base only when a second value object reuses the same rule.

---

## 4. File-by-file move map

Use `git mv` for pure moves so history follows the file.

| Current path | Target path | What changes |
|---|---|---|
| `main.py` | `main.py` | Becomes 10 lines: call `main_flow.http.run_http()`; drop the `print` calls |
| `composition_root/setup/setup.py` | `main_flow/http.py` + `main_flow/logging_setup.py` | Split: orchestration vs logging. Directory `composition_root/setup/` is deleted |
| `composition_root/containers/container.py` | `composition_root/containers/http_container.py` | `Container` → `HttpContainer`; `BuildContainer` → `new_http_container(server_cfg, microphone_cfg)`; no hardcoded values |
| `composition_root/dependencies/microphone_dependency.py` | `composition_root/dependencies/microphone_dependencies.py` | Split into small factories (`new_audio_capture`, `new_microphone_service`, `new_http_app`) |
| `application/dtos/stream_dtos.py` | `application/dtos/start_stream_inbound.py` | `StartStreamCommand` → `StartStreamInboundDTO` |
| *(new)* | `application/dtos/stream_outbound.py` | `StreamOutboundDTO(sample_rate, stream)` — see §5.2 |
| `application/ports/service_port.py` | `application/ports/inbound/microphone_streaming_port.py` | `ServicePort` → `MicrophoneStreamingPort` |
| `application/ports/microphone_port.py` | `application/ports/outbound/audio_capture_port.py` + `audio_stream_port.py` | `MicrophonePort` → `AudioCapturePort`; `AudioStream` → `AudioStreamPort` (one interface per file) |
| `application/services/microphone_service.py` | same path | Stops wrapping in `RuntimeError`; depends on renamed ports/DTOs |
| *(new)* | `application/errors.py` | Application-level exceptions |
| `infrastructure/inbound/http/routes/microphone_routes.py` | `infrastructure/inbound/http/http_handler.py`, `http_error_mapper.py`, `http_envelope.py` | Closure → handler class; error translation extracted |
| `infrastructure/outbound/sounddevice_microphone.py` | `infrastructure/outbound/sounddevice_capture/…` (3 files) | Split stream / capture / error mapper; translate driver errors |
| *(new)* | `infrastructure/config/server_config.py`, `microphone_config.py` | Typed env config |
| `domain/**` | unchanged | Optional: `SAMPLE_WIDTH_BYTES` → `domain/rules.py` |
| `tests/…` | mirrored, see §6 | Follow the renames; add `tests/composition_root/` |
| `docs/general.md` | `docs/old/general.md` | Preserve, do not delete |
| `README.md` | `docs/old/README.legacy.md`, then write a new `README.md` | Old one describes the deleted design |

---

## 5. Code reorganization, layer by layer

### 5.1 Domain — keep as is

Nothing structural changes. Two notes:

- `InvalidAudioFormat`, `CaptureAlreadyActive`, `CaptureNotActive` are domain vocabulary describing what happened to the use case, not which library failed. That matches the standard's error-ownership rule. Keep them.
- The double inheritance (`DomainError, ValueError`) exists for backward compatibility with pre-refactor callers. Keep it until D5 in §9 is decided.
- `[MANDATORY]` still holds: `domain/` imports only the stdlib and itself. The existing architecture test covers it.

### 5.2 Application

**Errors** (`application/errors.py`) — new. These are the targets that outbound adapters translate driver failures into:

```python
class ApplicationError(Exception):
    """Base class for failures of a use case that are not business-rule violations."""


class MicrophoneUnavailable(ApplicationError):
    """No capture device or format could be opened."""


class StreamCloseFailed(ApplicationError, RuntimeError):
    """The device could not be released cleanly.

    Also a RuntimeError so callers written against the previous behaviour keep working.
    """
```

**DTOs** — plain frozen data holders, no methods, one per file (`[DEFAULT]`):

```python
# application/dtos/start_stream_inbound.py
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StartStreamInboundDTO:
    """Carries the parameters of the start-streaming use case into the application layer."""

    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
```

```python
# application/dtos/stream_outbound.py
from collections.abc import AsyncIterable
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StreamOutboundDTO:
    """A live stream handed back to an inbound adapter, plus the rate actually negotiated."""

    sample_rate: int
    stream: AsyncIterable[bytes]
```

Why `StreamOutboundDTO` exists: today the inbound port returns `AudioStream`, a type defined next to the *outbound* port, and the HTTP layer reads `.sample_rate` off a driven-port object. The DTO gives inbound adapters their own boundary shape. **Anti-over-engineering note:** this is a `[DEFAULT]` refinement, not a boundary violation, because both types live in `application`. If you would rather not add it, keep returning `AudioStreamPort` from the inbound port and only do the rename. Tracked as D3.

**Ports** — one interface per file, named `<Concept>Port`:

```python
# application/ports/inbound/microphone_streaming_port.py
from abc import ABC, abstractmethod

from application.dtos.start_stream_inbound import StartStreamInboundDTO
from application.dtos.stream_outbound import StreamOutboundDTO


class MicrophoneStreamingPort(ABC):
    """What the outside world may ask of the application."""

    @abstractmethod
    async def start_stream(self, request: StartStreamInboundDTO) -> StreamOutboundDTO: ...

    @abstractmethod
    async def stop_stream(self) -> None: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def current_stream(self) -> StreamOutboundDTO: ...
```

```python
# application/ports/outbound/audio_stream_port.py
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class AudioStreamPort(ABC):
    """A live stream of mono 16-bit PCM chunks coming from an opened device."""

    @property
    @abstractmethod
    def sample_rate(self) -> int: ...

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[bytes]: ...

    @abstractmethod
    async def close(self) -> None:
        """Release the device. Must be idempotent. Raises StreamCloseFailed on failure."""
```

```python
# application/ports/outbound/audio_capture_port.py
from abc import ABC, abstractmethod

from application.ports.outbound.audio_stream_port import AudioStreamPort
from domain.value_objects.audio_format import AudioFormat


class AudioCapturePort(ABC):
    """What the application needs from a capture device."""

    @abstractmethod
    async def open_stream(self, audio_format: AudioFormat) -> AudioStreamPort:
        """Open the device as close to ``audio_format`` as the hardware allows.

        Raises MicrophoneUnavailable if no working device/format can be opened.
        """
```

Port rules that apply: ports expose only domain types or application DTOs; never FastAPI, starlette, sounddevice, numpy or any transport type. Inbound ports are implemented only by `application/services/`; outbound ports only by `infrastructure/outbound/`.

**Service** — the shape stays the same; the changes are small:

- Constructor takes `capture: AudioCapturePort` (renamed from `device: MicrophonePort`).
- `start_stream` accepts `StartStreamInboundDTO` and returns `StreamOutboundDTO(sample_rate=stream.sample_rate, stream=stream)`.
- `stop_stream` **no longer wraps** `close()` errors in `RuntimeError`. The adapter already translates them to `StreamCloseFailed`, so the service just lets it propagate after leaving the domain state consistent.
- `current_stream` builds the outbound DTO from the held `AudioStreamPort`.
- Keep the `asyncio.Lock` and the `logging` calls exactly as they are.

Forbidden in `application/`: FastAPI, starlette, pydantic, uvicorn, sounddevice, numpy, httpx, anything from `infrastructure` or `composition_root`, `print()`.

### 5.3 Infrastructure — inbound (HTTP)

Replace the `build_microphone_router` closure by a handler class constructed with the inbound port (`[DEFAULT]`: never a module-level global port).

```python
# infrastructure/inbound/http/http_handler.py
import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from application.dtos.start_stream_inbound import StartStreamInboundDTO
from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from infrastructure.inbound.http.http_envelope import failure, success

logger = logging.getLogger(__name__)
_DEFAULTS = StartStreamInboundDTO()


class StartStreamBody(BaseModel):
    """HTTP transport model for POST /start. Never crosses into application/."""

    sample_rate: int = _DEFAULTS.sample_rate
    channels: int = _DEFAULTS.channels
    chunk_size: int = _DEFAULTS.chunk_size


class MicrophoneHandler:
    """Decode → call the inbound port → map error or encode response. No business rules."""

    def __init__(self, port: MicrophoneStreamingPort) -> None:
        self._port = port
        self.router = APIRouter()
        self.router.add_api_route("/start", self.handle_start, methods=["POST"])
        self.router.add_api_route("/stop", self.handle_stop, methods=["POST"])
        self.router.add_api_route("/available", self.handle_available, methods=["GET"])
        self.router.add_api_route("/stream", self.handle_stream, methods=["GET"])
        self.router.add_api_route("/health", self.handle_health, methods=["GET"], tags=["Health"])

    async def handle_start(self, body: StartStreamBody) -> JSONResponse:
        try:
            result = await self._port.start_stream(
                StartStreamInboundDTO(
                    sample_rate=body.sample_rate,
                    channels=body.channels,
                    chunk_size=body.chunk_size,
                )
            )
        except Exception as error:
            return failure("start_stream", "Failed to start microphone stream", error)
        return success(
            "start_stream",
            "Microphone stream started successfully",
            {"sample_rate": result.sample_rate},
        )

    # handle_stop / handle_available / handle_stream / handle_health follow the same pattern,
    # moving the current route bodies over unchanged (same JSON envelope, same headers on /stream).
```

`http_envelope.py` holds the current `_success` / `_failure` helpers (renamed without the underscore because they are now imported). `failure()` asks `http_error_mapper.map_error(error)` for the status code instead of hardcoding 500:

```python
# infrastructure/inbound/http/http_error_mapper.py
from fastapi import status


def map_error(error: Exception) -> int:
    """Translate an application/domain error into an HTTP status code.

    Behaviour-preserving default: every failure is 500, exactly as before the refactor.
    To adopt the natural mapping (decision D4), add:
        InvalidAudioFormat      -> 422
        CaptureAlreadyActive    -> 409
        CaptureNotActive        -> 409
        MicrophoneUnavailable   -> 503
    """
    return status.HTTP_500_INTERNAL_SERVER_ERROR
```

Rules that stay in force: the handler never contains a business rule; it does not import `infrastructure.outbound` or `composition_root`; the pydantic body model stays in infrastructure. Inline `Any` (used for the envelope `data` field) is tolerated only in `infrastructure/`, with a justification comment on the line above (`[DEFAULT]`).

### 5.4 Infrastructure — outbound (sounddevice)

Split the 208-line module by responsibility inside `infrastructure/outbound/sounddevice_capture/`. The folder is deliberately **not** called `sounddevice/`, so nobody confuses it with the third-party package.

| File | Contents |
|---|---|
| `sounddevice_audio_stream.py` | `SoundDeviceAudioStream(AudioStreamPort)` — the async iterator over `RawInputStream`, the level meter, `close()` |
| `sounddevice_audio_capture.py` | `SoundDeviceAudioCapture(AudioCapturePort)` — device discovery, format fallback loop using `domain.operations.format_negotiation`, opening the raw stream |
| `sounddevice_error_mapper.py` | `map_open_error(error) -> MicrophoneUnavailable`, `map_close_error(error) -> StreamCloseFailed` |

Error translation is the one *behavioural* addition. The standard is explicit that an adapter never lets a raw driver error cross the port:

```python
# infrastructure/outbound/sounddevice_capture/sounddevice_error_mapper.py
from application.errors import MicrophoneUnavailable, StreamCloseFailed


def map_open_error(error: Exception) -> MicrophoneUnavailable:
    return MicrophoneUnavailable(f"Could not open a microphone stream: {error}")


def map_close_error(error: Exception) -> StreamCloseFailed:
    return StreamCloseFailed(f"Failed to stop microphone stream: {error}")
```

Usage in the adapter: catch the driver failure at the `open_stream` boundary and `raise map_open_error(error) from error`; in `SoundDeviceAudioStream.close()` do the same with `map_close_error`. `from error` preserves the root cause, which is the Python equivalent of `JoinErrors`.

Keep `sounddevice` / `numpy` imports confined to this folder. The SDK handle is constructor-injected or module-imported here only; the adapter never returns `sd.*` types.

### 5.5 Infrastructure — config

The composition root and `main_flow` must stop reading the environment ad hoc. Add one config class per bounded concern in `infrastructure/config/`. Standard library only; no new dependency (decision D2).

```python
# infrastructure/config/server_config.py
import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ServerConfig:
    service_name: str
    host: str
    port: int
    log_level: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "ServerConfig":
        return cls(
            service_name=env.get("SERVICE_NAME", "Microphone Microservice"),
            host=env.get("SERVICE_HOST", "127.0.0.1"),
            port=int(env.get("SERVICE_PORT", "8000")),
            log_level=env.get("LOG_LEVEL", "INFO"),
        )
```

```python
# infrastructure/config/microphone_config.py
import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class MicrophoneConfig:
    fallback_sample_rate: int
    target_keywords: tuple[str, ...]
    show_meter: bool

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "MicrophoneConfig":
        raw_keywords = env.get("MICROPHONE_TARGET_KEYWORDS", "")
        return cls(
            fallback_sample_rate=int(env.get("MICROPHONE_FALLBACK_SAMPLE_RATE", "16000")),
            target_keywords=tuple(k.strip() for k in raw_keywords.split(",") if k.strip()),
            show_meter=env.get("MICROPHONE_SHOW_METER", "true").lower() in {"1", "true", "yes"},
        )
```

Passing `env` as a mapping makes the classes unit-testable without touching `os.environ`. Secrets never get a literal default.

Environment reference (mirror it in `.env.example`, no real secrets):

| Variable | Required | Default | Used by |
|---|---|---|---|
| `SERVICE_NAME` | No | `Microphone Microservice` | `ServerConfig` |
| `SERVICE_HOST` | No | `127.0.0.1` | `ServerConfig` |
| `SERVICE_PORT` | No | `8000` | `ServerConfig` |
| `LOG_LEVEL` | No | `INFO` | `ServerConfig` / `logging_setup` |
| `MICROPHONE_FALLBACK_SAMPLE_RATE` | No | `16000` | `MicrophoneConfig` |
| `MICROPHONE_TARGET_KEYWORDS` | No | *(empty)* | `MicrophoneConfig` (comma-separated) |
| `MICROPHONE_SHOW_METER` | No | `true` | `MicrophoneConfig` |

Two existing `.env` issues to fix while you are here:

- `LOG_LEVEL=TRACE`, `WARN` are not `logging` level names, so today `getattr(logging, ...)` silently falls back to `INFO`. Normalize in `logging_setup.py`: `TRACE → DEBUG`, `WARN → WARNING`.
- `APP_ENV`, `VSCODE_ENV`, `VSCODE_LAUNCH_PROFILE` are VS Code launch helpers and `APP_ENV` is never read. `MICROPHONE_API_KEY` is read nowhere and no authentication exists (decision D6).

### 5.6 Composition root

`composition_root/` keeps only `containers/` and `dependencies/`. It is the only package allowed to import `infrastructure.inbound`, `infrastructure.outbound`, `application` and `domain` together.

```python
# composition_root/dependencies/microphone_dependencies.py
from fastapi import FastAPI

from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.services.microphone_service import MicrophoneService
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.inbound.http.http_handler import MicrophoneHandler
from infrastructure.outbound.sounddevice_capture.sounddevice_audio_capture import (
    SoundDeviceAudioCapture,
)


def new_audio_capture(cfg: MicrophoneConfig) -> AudioCapturePort:
    return SoundDeviceAudioCapture(
        default_fallback_rate=cfg.fallback_sample_rate,
        target_keywords=cfg.target_keywords,
        show_meter=cfg.show_meter,
    )


def new_microphone_service(capture: AudioCapturePort, name: str) -> MicrophoneStreamingPort:
    return MicrophoneService(capture=capture, name=name)


def new_http_app(port: MicrophoneStreamingPort, name: str) -> FastAPI:
    app = FastAPI(
        title=name,
        description=f"HTTP adapter exposing {name}",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.include_router(MicrophoneHandler(port).router)
    return app
```

```python
# composition_root/containers/http_container.py
from dataclasses import dataclass

from fastapi import FastAPI

from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from composition_root.dependencies import microphone_dependencies as deps
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig


@dataclass(slots=True, frozen=True)
class HttpContainer:
    app: FastAPI
    microphone: MicrophoneStreamingPort  # kept so main_flow can release the device on shutdown


def new_http_container(server_cfg: ServerConfig, microphone_cfg: MicrophoneConfig) -> HttpContainer:
    capture = deps.new_audio_capture(microphone_cfg)
    service = deps.new_microphone_service(capture, server_cfg.service_name)
    app = deps.new_http_app(service, server_cfg.service_name)
    return HttpContainer(app=app, microphone=service)
```

Containers stay declarative wiring; dependencies hold the construction logic. One container per initialization configuration (`HttpContainer` now; a `WorkerContainer` would be added only if a worker entry point appears).

### 5.7 Entry point — `main.py` and `main_flow/`

`main_flow` owns, in order: parse config → build container → start serving → graceful shutdown. It contains no business logic and does **not** import `infrastructure.inbound` or `infrastructure.outbound` (only `infrastructure.config` and `composition_root`).

```python
# main.py
import asyncio

from main_flow.http import run_http


def main() -> None:
    try:
        asyncio.run(run_http())
    except KeyboardInterrupt:
        pass  # Ctrl+C: uvicorn already shut down gracefully and cleanup ran


if __name__ == "__main__":
    main()
```

```python
# main_flow/http.py
import logging

import uvicorn

from composition_root.containers.http_container import HttpContainer, new_http_container
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig
from main_flow.logging_setup import configure_logging

logger = logging.getLogger(__name__)


async def run_http() -> None:
    server_cfg = ServerConfig.from_env()
    microphone_cfg = MicrophoneConfig.from_env()
    configure_logging(server_cfg.log_level)

    container = new_http_container(server_cfg, microphone_cfg)
    server = uvicorn.Server(
        uvicorn.Config(container.app, host=server_cfg.host, port=server_cfg.port)
    )
    logger.info("%s - starting server on %s:%s", server_cfg.service_name, server_cfg.host, server_cfg.port)
    try:
        await server.serve()  # returns after SIGINT/SIGTERM
    finally:
        await _cleanup(container)


async def _cleanup(container: HttpContainer) -> None:
    logger.info("Server stopped; releasing microphone")
    try:
        await container.microphone.stop_stream()
    except Exception:
        logger.exception("Failed to stop microphone stream during cleanup")
```

`logging_setup.py` is the current `configure_logging()` from `setup.py`, taking the level as an argument and normalizing `TRACE`/`WARN`.

Nothing else references `composition_root/setup/`: `.vscode/launch.json` already points at `main.py`, so it does not change.

---

## 6. Tests

Mirror the new layout, using the standard's boundary per layer.

| Tests folder | Follows | Changes |
|---|---|---|
| `tests/domain/` | `domain/` | None. Pure unit tests, no I/O |
| `tests/application/test_microphone_service.py` | service | Fakes implement `AudioCapturePort` / `AudioStreamPort`; use `StartStreamInboundDTO`; the "close fails" case now has the fake raise `StreamCloseFailed` and the service just propagates it |
| `tests/infrastructure/test_http_handler.py` (was `test_microphone_routes.py`) | handler | Build `MicrophoneHandler(service)`; assertions on the JSON envelope stay identical |
| `tests/infrastructure/test_http_error_mapper.py` | mapper | New, tiny |
| `tests/infrastructure/test_sounddevice_audio_capture.py` (was `test_sounddevice_microphone.py`) | adapter | Still runs against a fake `sounddevice` module; add a case asserting a driver error becomes `MicrophoneUnavailable` and `close()` errors become `StreamCloseFailed` |
| `tests/infrastructure/test_config.py` | config | New: defaults, overrides, keyword parsing, boolean parsing, via the `env` mapping |
| `tests/composition_root/test_http_container.py` | wiring | New smoke test: `new_http_container(...)` returns an app whose `/health` responds, with a fake `sounddevice` module injected |
| `tests/architecture/test_dependency_rules.py` | all | Update `OWN_PACKAGES` to include `main_flow`; add the rules below |
| `tests/simple.py` | e2e | Import `new_http_container` and the config classes instead of `BuildContainer`; still needs a real microphone |

Add to the architecture test:

- `main_flow` must not import `infrastructure.inbound` / `infrastructure.outbound`.
- `infrastructure.inbound` and `infrastructure.outbound` must not import each other (already enforced).
- `application/`, `domain/`, `composition_root/` contain no `print(` calls (AST check for `Call(Name("print"))`).
- No module or package named `utils`, `common` or `helpers` anywhere under the source roots.

Do not introduce mock frameworks: the existing hand-written fakes are the recommended style.

---

## 7. Root files, tooling and docs

1. **`pyproject.toml`** (tool configuration only; nothing is packaged):

   ```toml
   [tool.ruff]
   line-length = 100
   target-version = "py311"

   [tool.ruff.lint]
   select = ["E", "F", "I", "B", "UP"]

   [tool.black]
   line-length = 100
   target-version = ["py311"]

   [tool.mypy]
   python_version = "3.11"
   strict = true
   explicit_package_bases = true
   mypy_path = "."
   exclude = ["^windows/", "^tests/"]

   [[tool.mypy.overrides]]
   module = ["sounddevice", "numpy.*"]
   ignore_missing_imports = true
   ```

   The project runs on Python 3.14 today, so `py311` is a floor, not the runtime.

2. **`requirements.windows.txt`**: remove `soundfile` (unused), add `httpx` (used by `tests/simple.py` and FastAPI's `TestClient`), add `ruff`, `black`, `mypy` under a `#TOOLING` block. Pin versions once the set is verified (the `.pyc` files show pytest 9.0.x and Python 3.14).

3. **`__init__.py`**: add an empty `__init__.py` to `domain/`, `application/`, `infrastructure/`, `main_flow/`, `composition_root/` and every sub-folder. There are none today (implicit namespace packages); mypy and ruff's import sorting need them or the `explicit_package_bases` flag above. Keep the existing "no relative imports" rule.

4. **`.env.example`** (new) with the table from §5.5, and change `.gitignore` from `.env*` to:

   ```gitignore
   .env*
   !.env.example
   ```

   Otherwise `.env.example` can never be committed. `.env.staging` / `.env.production` remain ignored and must never hold secrets.

5. **Docs**:
   - `docs/old/general.md`, `docs/old/README.legacy.md` (moved, not deleted).
   - `docs/architecture/` — put the "Clean Architecture after refactor" write-up (the existing project document `claude/architecture.md` is a good starting point) and update its layout and "known debt" lists to match §3.
   - Write a new `README.md`: what the service does, how to run it, endpoints, env vars, how to run the tests. The old README's endpoint reference (`/start`, `/stop`, `/available`, `/stream`, `/health`) is still accurate and can be reused; everything about DTOs, mappers and adapters is not.

6. **`.engram/`** (project-local; never duplicate the global standard here):

   | File | Content |
   |---|---|
   | `project.md` | What the service is; the omitted Go-tree items from §3 and why |
   | `architecture.md` | The layer diagram and target tree of §3 |
   | `constraints.md` | Windows-only audio backend; needs a physical microphone for e2e; mono 16-bit PCM |
   | `decisions.md` | D1–D3, D5 from §9 |
   | `overrides.md` | Empty unless a MANDATORY rule is deliberately broken. This plan needs no overrides |
   | `specs/<id>/` | One entry per phase below if you want it tracked (`proposal.md`, `tasks.md`, `expected-results.md`) |

7. **Repository hygiene** (no code impact, but keep them out of the repo): the `windows/` virtualenv (already git-ignored; consider moving it outside the project or renaming to `.venv-windows`, and update `.vscode/launch.json` `"python"` accordingly), `.tmp_pydeps.tar`, and the stale `composition_root/runtime/` and `application/events/` folders that only contain `__pycache__`.

---

## 8. Execution order

Each phase should leave `pytest` green so a failure is easy to bisect. Commit at the end of every phase (Conventional Commits, e.g. `refactor(application): split ports into inbound/outbound`).

| Phase | Work | Check |
|---|---|---|
| 0 | Commit the current working tree as a checkpoint | `git status` clean; `pytest` passes |
| 1 | **Tooling**: `pyproject.toml`, requirements fix, `__init__.py` files, `.env.example` + `.gitignore` | `pip install -r requirements.windows.txt`, `pytest` still passes |
| 2 | **Application**: `errors.py`, DTO split, `ports/inbound` + `ports/outbound` renames, service update. Update `tests/application/` in the same commit | `pytest tests/application tests/domain tests/architecture` |
| 3 | **Outbound adapter**: split `sounddevice_capture/`, add error mapper, add the two translation tests | `pytest tests/infrastructure` |
| 4 | **Inbound adapter**: `MicrophoneHandler`, `http_envelope.py`, `http_error_mapper.py` (default still 500) | Handler tests pass with unchanged JSON assertions |
| 5 | **Config**: `infrastructure/config/`, `test_config.py` | Config tests pass |
| 6 | **Composition root + entry point**: new dependencies/container, `main_flow/`, thin `main.py`, delete `composition_root/setup/`, update `tests/simple.py`, add wiring test | `pytest`; `python main.py` starts and `Ctrl+C` exits cleanly |
| 7 | **Architecture tests, docs and `.engram/`**: extra rules of §6, move old docs, write new README | `pytest tests/architecture` |
| 8 | **Cleanup**: remove stale folders and `.tmp_pydeps.tar`; run the full verification of §10 | All green |

Phases 2–6 can each be a single pull request. Because most of the work is renames plus small edits, prefer `git mv` first, then edit.

---

## 9. Decisions to record or confirm

These are places where the standard leaves more than one valid option. They belong in `.engram/decisions.md`; D6 needs an answer from you.

| ID | Decision | Recommendation |
|---|---|---|
| D1 | **Do not name the entry folder `cmd/`.** The Go folder name is `[DEFAULT]`. In Python, a top-level `cmd` package shadows the stdlib `cmd` module, which `pdb` and `code` import, so the debugger breaks when run from the repo root | Keep `main.py` + `main_flow/` at the root. The invariant (bootstrapping separate from business logic) is preserved |
| D2 | Config library | Standard library dataclasses (no new dependency). `pydantic-settings` is the closest equivalent to Go's `envconfig` if you prefer declarative fields; switching later only touches `infrastructure/config/` |
| D3 | Add `StreamOutboundDTO` so the inbound port stops returning an outbound-port type | Recommended, but optional under the anti-over-engineering principle |
| D4 | HTTP status mapping: keep "everything is 500" (behaviour-preserving) or adopt 422 / 409 / 503 | Keep 500 during the migration so tests and clients see no change; switch in a separate, explicitly breaking-for-clients commit |
| D5 | Keep `DomainError` also inheriting `ValueError` / `RuntimeError` | Keep until you confirm no caller depends on the builtin types, then drop |
| D6 | `MICROPHONE_API_KEY` is defined in three `.env` files and read nowhere | Either implement API-key authentication (a new feature, its own spec) or remove the variable now. The standard forbids placeholder configuration that does nothing. **Needs your decision** |

No `[MANDATORY]` rule requires an override. The one MANDATORY gap that exists today (G3, driver errors crossing the port) is fixed by this plan rather than excused.

---

## 10. Verification checklist

Baseline commands (Python equivalent of `go test / vet / gofmt`):

```bash
pytest
mypy .
ruff check .
black --check .
```

Structural checks that should hold when the migration is complete:

- `grep -rn "print(" application domain composition_root main_flow infrastructure` returns nothing.
- `grep -rnE "^(from|import) (fastapi|starlette|pydantic|uvicorn|sounddevice|numpy|httpx)" application domain` returns nothing.
- `grep -rn "infrastructure.outbound" --include=*.py .` matches only `composition_root/` (and `tests/`).
- No file or folder named `utils`, `common` or `helpers` exists.
- `composition_root/` contains only `containers/` and `dependencies/`.
- Every environment variable read in the code appears in `.env.example`, and vice versa.
- `python main.py` starts, `GET /health` returns the standard envelope, `Ctrl+C` stops the server and logs "releasing microphone".
- On the Windows machine with a real microphone: `python tests/simple.py` passes. This has never been run against the refactored code, and the sounddevice adapter is otherwise only tested against a fake module.

---

## 11. Known behaviour that must not change during this migration

Carried over from the first pass, and the reason phases keep the handler tests' JSON assertions untouched:

- Every failure returns HTTP 500 with the envelope `action / status / status_code / message / timestamp / data`.
- `POST /start` returns JSON; audio is read from `GET /stream`, with the `X-*` response headers.
- `GET /available` means "a stream is active".
- Requests with `channels > 1` are still delivered as mono.
- A client disconnecting from `/stream` still ends the shared stream until stop + start.

Remaining debt that is deliberately *not* part of this migration (tracked in `claude/architecture.md`): the disconnected-stream domain state, silent stereo→mono mixdown not reported to the client, and blocking `sounddevice` calls on the event loop.
