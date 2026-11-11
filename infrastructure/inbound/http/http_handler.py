"""HTTP inbound adapter: declares the endpoints and wires each one to its route.

No request logic of its own.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from application.dtos.inbound.start_stream_inbound import StartStreamInboundDTO
from application.dtos.outbound.stream_outbound import StreamOutboundDTO
from application.ports.inbound.microphone_inbound_port import MicrophoneInboundPort
from application.ports.service.microphone_service_port import MicrophoneServicePort
from infrastructure.inbound.http.routes.available import handle_available
from infrastructure.inbound.http.routes.get_stream import handle_get_stream
from infrastructure.inbound.http.routes.health import handle_health
from infrastructure.inbound.http.routes.start_stream import StartStreamBody, handle_start_stream
from infrastructure.inbound.http.routes.stop import handle_stop


class MicrophoneHandler(MicrophoneInboundPort):
    """The HTTP inbound adapter. It declares which endpoints exist and wires each to its function in
    ``routes/``; the answers and the error mapping live in ``response/`` and ``errors/``.
    Its operations are those of ``MicrophoneInboundPort`` (DTOs, no HTTP types) and the routes call
    them."""

    def __init__(self, service: MicrophoneServicePort) -> None:
        self._service = service
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self) -> None:
        inbound: MicrophoneInboundPort = self
        add = self.router.add_api_route

        async def health() -> JSONResponse:
            return await handle_health(inbound)

        async def available() -> JSONResponse:
            return await handle_available(inbound)

        async def stop() -> JSONResponse:
            return await handle_stop(inbound)

        async def start(body: StartStreamBody) -> JSONResponse:
            return await handle_start_stream(body, inbound)

        async def get_stream(
            sample_rate: int | None = None, chunk_size: int | None = None
        ) -> StreamingResponse | JSONResponse:
            return await handle_get_stream(inbound, sample_rate)

        add("/health", health, methods=["GET"], tags=["Health"])
        add("/available", available, methods=["GET"])
        add("/start", start, methods=["POST"])
        add("/stop", stop, methods=["POST"])
        add("/stream", get_stream, methods=["GET"], response_model=None)

    # --- MicrophoneInboundPort: the operations every inbound adapter offers -----------------------

    def health(self) -> bool:
        return True

    async def check_device(self) -> tuple[bool, str | None]:
        return await self._service.check_device()

    async def start_stream(self, request: StartStreamInboundDTO) -> StreamOutboundDTO:
        return await self._service.start_stream(request)

    async def stop_stream(self) -> None:
        await self._service.stop_stream()

    def current_stream(self) -> StreamOutboundDTO:
        return self._service.current_stream()
