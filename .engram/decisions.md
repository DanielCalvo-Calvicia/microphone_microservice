# Decisions

- D1: No `cmd/` folder (shadows stdlib `cmd`); entry point is `main.py` + `main_flow/`.
- D2: Config is stdlib frozen dataclasses in `infrastructure/config/`.
- D3: `StreamOutboundDTO` added so the inbound port does not return an outbound-port type.
- D4: HTTP status mapping stays "everything is 500" (`http_error_mapper.py`) until clients are ready.
- D5: `DomainError` keeps its builtin base classes for backward compatibility.
- D6: OPEN. `MICROPHONE_API_KEY` in `.env*` is read nowhere; implement auth or remove it.
