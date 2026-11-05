# 10 — Architecture

> Depends on: 05, 09. The full description is [../architecture/architecture.md](../architecture/architecture.md).

| Topic | Answer |
|---|---|
| Style | Layered / hexagonal: `composition_root -> infrastructure -> application -> domain`, dependencies inward only |
| Execution flows | One: the HTTP service (`main.py` -> `main_flow/http.py` -> uvicorn) |
| Driving port | `MicrophoneStreamingPort` (`start_stream`, `stop_stream`, `is_available`, `current_stream`, `check_device`) |
| Driven ports | `AudioCapturePort` (`open_stream`, `check_device`), `AudioStreamPort` (`sample_rate`, async iteration, `on_terminated`, `close`) |
| Adapters | Inbound: FastAPI handler, envelope, error mapper, NDJSON framing. Outbound: sounddevice (driver protocol, device selector, stream, error mapper) |
| Composition | `composition_root/dependencies/microphone_dependencies.py` (`new_audio_capture`, `new_microphone_service`, `new_http_app`) and `containers/http_container.py` |
| Enforcement | `tests/architecture/test_dependency_rules.py` parses imports against the layer table |
| Concurrency | One asyncio loop; `start` and `stop` under a lock; blocking device calls through `asyncio.to_thread` |
| Where it deviates from the workspace standard | It does not: the layout is the one `../CLAUDE.md` requires. The shared package `shared_logging` and `contracts` are bundled, not imported across services |
| Where the structure is thin | `application/services/utterance_stream.py` is the only application code that knows about utterances; the segmenter itself is in the domain |
