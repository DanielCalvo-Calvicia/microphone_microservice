
from typing import Any

from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse, JSONResponse

import time

from application.ports.adapter_inbound_port import AdapterInboundPort
from application.ports.service_port import ServicePort

from application.dtos.adapter_inbound_dtos import (
    StartMicrophoneStreamRequestDto,
    StartMicrophoneStreamResponseDto,
    StopMicrophoneStreamRequestDto,
    StopMicrophoneStreamResponseDto,
    MicrophoneAvailabilityRequestDto,
    MicrophoneAvailabilityResponseDto,
    GetStreamRequestDto,
    GetStreamResponseDto
)

from application.dtos.mapper.adapter_inbound_to_service import (
    map_adapter_to_service_start_request,
    map_adapter_to_service_stop_request,
    map_adapter_to_service_availability_request,
    map_adapter_to_service_get_stream_request
)

from application.dtos.mapper.service_to_adapter_inbound import (
    map_service_to_adapter_start_response,
    map_service_to_adapter_stop_response,
    map_service_to_adapter_availability_response,
    map_service_to_adapter_get_stream_response
)

class FastApiAdapter(AdapterInboundPort):
    def __init__(self, service_port: ServicePort, app: FastAPI):
        self.service_port = service_port
        self.app = app

        print("[http] FastApiAdapter initialized")
        self.register_routes(self.app)

    def register_routes(self, app: FastAPI):
        print("[http] Registering HTTP routes")
        @app.post("/start", status_code=status.HTTP_200_OK)
        async def handle_start_stream(request: StartMicrophoneStreamRequestDto):
            print(
                "[http] POST /start received "
                f"sample_rate={request.sample_rate}, channels={request.channels}, "
                f"chunk_size={request.chunk_size}"
            )
            try:
                response = await self.start_stream(request)
                print(f"[http] POST /start succeeded sample_rate={response.sample_rate}")

                http_response = JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "action": "start_stream",
                        "status": "success",
                        "status_code": status.HTTP_200_OK,
                        "message": "Microphone stream started successfully",
                        "timestamp": time.time(),
                        "data": {
                            "sample_rate": response.sample_rate,
                        },
                    }
                )
                return http_response
            except Exception as e:
                print(f"[http] POST /start failed: {e!r}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "action": "start_stream",
                        "status": "error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": f"Failed to start microphone stream: {str(e)}",
                        "timestamp": time.time(),
                        "data": str(e)
                    }
                )
            
            
        @app.post("/stop", status_code=status.HTTP_200_OK)
        async def handle_stop_stream(request: StopMicrophoneStreamRequestDto):
            print("[http] POST /stop received")
            try:
                response = await self.stop_stream(request)
                print(f"[http] POST /stop succeeded success={response.success}")
                http_response = JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "action": "stop_stream",
                        "status": "success",
                        "status_code": status.HTTP_200_OK,
                        "message": "Microphone stream stopped successfully",
                        "timestamp": time.time(),
                        "data": response.success
                    }
                )
                return http_response
            except Exception as e:
                print(f"[http] POST /stop failed: {e!r}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "action": "stop_stream",
                        "status": "error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": f"Failed to stop microphone stream: {str(e)}",
                        "timestamp": time.time(),
                        "data": str(e)
                    }
                )

        @app.get("/available", status_code=status.HTTP_200_OK)
        async def handle_check_availability():
            print("[http] GET /available received")
            try:
                request_dto = MicrophoneAvailabilityRequestDto()
                response = await self.is_available(request_dto)
                print(f"[http] GET /available succeeded is_available={response.is_available}")
                http_response = JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "action": "check_availability",
                        "status": "success",
                        "status_code": status.HTTP_200_OK,
                        "message": "Microphone availability checked successfully",
                        "timestamp": time.time(),
                        "data": response.is_available
                    }
                )
                return http_response
            except Exception as e:
                print(f"[http] GET /available failed: {e!r}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "action": "check_availability",
                        "status": "error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": f"Failed to check microphone availability: {str(e)}",
                        "timestamp": time.time(),
                        "data": str(e)
                    }
                )
        @app.get("/stream", status_code=status.HTTP_200_OK)
        async def handle_get_stream():
            print("[http] GET /stream received")
            try:
                request_dto = GetStreamRequestDto()
                response = await self.mic_stream(request_dto)
                print(f"[http] GET /stream succeeded sample_rate={response.sample_rate}; returning StreamingResponse")
                http_response = StreamingResponse(
                    response.stream,
                    media_type="application/octet-stream",
                    status_code=status.HTTP_200_OK,
                    headers={
                        "X-Sample-Rate": str(response.sample_rate),
                        "X-Action": "get_stream",
                        "X-Status": "success",
                        "X-Message": "Microphone stream retrieved successfully",
                        "X-Timestamp": str(time.time()),
                        "X-Sample-Rate": str(response.sample_rate),
                    }
                )
                return http_response
            except Exception as e:
                print(f"[http] GET /stream failed: {e!r}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "action": "get_stream",
                        "status": "error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": f"Failed to retrieve microphone stream: {str(e)}",
                        "timestamp": time.time(),
                        "data": str(e)
                    }
                )
        @app.get("/health", tags=["Health"])
        async def health_check():
            print("[http] GET /health received")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "action": "health_check",
                    "status": "success",
                    "status_code": status.HTTP_200_OK,
                    "message": "Service is healthy",
                    "timestamp": time.time(),
                    "data": None
                }
            )
    @property
    def get_app(self) -> Any:
        print("[http] get_app accessed")
        return self.app

    async def start_stream(self, request: StartMicrophoneStreamRequestDto) -> StartMicrophoneStreamResponseDto:
        print("[http] Adapter start_stream mapping inbound DTO to service DTO")
        
        service_request_dto = map_adapter_to_service_start_request(request)
        
        print("[http] Adapter start_stream calling service")
        service_response_dto = await self.service_port.start_stream(service_request_dto)

        print("[http] Adapter start_stream mapping service response to inbound DTO")
        adapter_response_dto = map_service_to_adapter_start_response(service_response_dto)

        print("[http] Adapter start_stream completed")
        return adapter_response_dto
    

    async def stop_stream(self, request: StopMicrophoneStreamRequestDto) -> StopMicrophoneStreamResponseDto:
        print("[http] Adapter stop_stream mapping inbound DTO to service DTO")
        service_request_dto = map_adapter_to_service_stop_request(request)
        print("[http] Adapter stop_stream calling service")
        service_response_dto = await self.service_port.stop_stream(service_request_dto)
        print("[http] Adapter stop_stream mapping service response to inbound DTO")
        adapter_response_dto = map_service_to_adapter_stop_response(service_response_dto)
        print("[http] Adapter stop_stream completed")
        return adapter_response_dto

    async def is_available(self, request: MicrophoneAvailabilityRequestDto) -> MicrophoneAvailabilityResponseDto:
        print("[http] Adapter is_available mapping inbound DTO to service DTO")
        service_request_dto = map_adapter_to_service_availability_request(request)
        print("[http] Adapter is_available calling service")
        service_response_dto = await self.service_port.is_available(service_request_dto)
        print("[http] Adapter is_available mapping service response to inbound DTO")
        adapter_response_dto = map_service_to_adapter_availability_response(service_response_dto)
        print("[http] Adapter is_available completed")
        return adapter_response_dto

    async def mic_stream(self, request: GetStreamRequestDto) -> GetStreamResponseDto:
        print("[http] Adapter mic_stream mapping inbound DTO to service DTO")
        service_request_dto = map_adapter_to_service_get_stream_request(request)
        print("[http] Adapter mic_stream calling service")
        service_response_dto = self.service_port.mic_stream(service_request_dto)
        print("[http] Adapter mic_stream mapping service response to inbound DTO")
        adapter_response_dto = map_service_to_adapter_get_stream_response(service_response_dto)
        print("[http] Adapter mic_stream completed")
        return adapter_response_dto
