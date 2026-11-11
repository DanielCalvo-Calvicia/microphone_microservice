# 10 — Architecture

> Depends on: 05, 09. The full description is [../architecture/architecture.md](../architecture/architecture.md).

| Topic | Answer |
|---|---|
| Style | Layered / hexagonal: `composition_root -> infrastructure -> application -> domain`, dependencies inward only |
| Execution flows | One: the HTTP service (`main.py` -> `main_flow/http.py` -> uvicorn) |
| Driving ports | `MicrophoneInboundPort` (`health`, `check_device`, `start_stream`, `stop_stream`, `current_stream`; the handler implements it) and `MicrophoneServicePort` (`start_stream`, `stop_stream`, `is_available`, `current_stream`, `check_device`; the service implements it) |
| Driven ports | `AudioCapturePort` (`open_stream`, `check_device`), `AudioStreamPort` (`sample_rate`, async iteration, `on_terminated`, `close`) |
| Adapters | Inbound: FastAPI handler, `routes/`, `response/` (envelope, NDJSON framing, headers), `errors/` (error mapper). Outbound: sounddevice (driver protocol, device selector, stream, error mapper) |
| Composition | `composition_root/dependencies/` (`audio_capture_dependency.py`, `microphone_service_dependency.py`, `http_app_dependency.py`: `new_audio_capture`, `new_microphone_service`, `new_http_app`) and `containers/http_container.py` |
| Enforcement | `tests/architecture/test_dependency_rules.py` parses imports against the layer table |
| Concurrency | One asyncio loop; `start` and `stop` under a lock; blocking device calls through `asyncio.to_thread` |
| Where it deviates from the workspace standard | It does not: the layout is the one `../CLAUDE.md` requires. The shared package `shared_logging` and `contracts` are bundled, not imported across services |
| Where the structure is thin | `application/services/utterance_stream.py` is the only application code that knows about utterances; the segmenter itself is in the domain |
