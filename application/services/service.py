from application.ports.service_port import ServicePort
from application.ports.adapter_outbound_port import AdapterOutboundPort
from application.dtos.services_dtos import (
    StartMicrophoneStreamRequestDto as ServiceDto_StartMicrophoneStreamRequestDto,
    StartMicrophoneStreamResponseDto as ServiceDto_StartMicrophoneStreamResponseDto,
    StopMicrophoneStreamRequestDto as ServiceDto_StopMicrophoneStreamRequestDto,
    StopMicrophoneStreamResponseDto as ServiceDto_StopMicrophoneStreamResponseDto,
    MicrophoneAvailabilityRequestDto as ServiceDto_MicrophoneAvailabilityRequestDto,
    MicrophoneAvailabilityResponseDto as ServiceDto_MicrophoneAvailabilityResponseDto,
    GetStreamRequestDto as ServiceDto_GetStreamRequestDto,
    GetStreamResponseDto as ServiceDto_GetStreamResponseDto
)

from application.dtos.mapper.service_to_adapter_outbound import (
    map_service_to_adapter_start_request,
    map_service_to_adapter_stop_request,
    map_service_to_adapter_availability_request,
    map_service_to_adapter_get_stream_request,
)
from application.dtos.mapper.adapter_outbound_to_service import (
    map_adapter_to_service_start_response,
    map_adapter_to_service_stop_response,
    map_adapter_to_service_availability_response,
    map_adapter_to_service_get_stream_response,
)

class MicrophoneService(ServicePort):
    def __init__(self, name: str, controller_port: AdapterOutboundPort):        
        self.name = name
        self.controller_port = controller_port
        print(f"[service] MicrophoneService initialized name={name!r}")

    async def start_stream(
        self, 
        request: ServiceDto_StartMicrophoneStreamRequestDto
    ) -> ServiceDto_StartMicrophoneStreamResponseDto:
        """Start the microphone stream."""
        print(
            "[service] start_stream received "
            f"sample_rate={request.sample_rate}, channels={request.channels}, "
            f"chunk_size={request.chunk_size}"
        )

        print("[service] start_stream mapping service DTO to outbound DTO")
        port_request_dto = map_service_to_adapter_start_request(request)
        
        print("[service] start_stream calling outbound adapter")
        port_response = await self.controller_port.start_stream(port_request_dto)

        print(
            "[service] start_stream mapping outbound response to service DTO "
            f"sample_rate={port_response.sample_rate}"
        )
        service_response = map_adapter_to_service_start_response(port_response)

        print("[service] start_stream completed")
        return service_response


    async def stop_stream(self, request: ServiceDto_StopMicrophoneStreamRequestDto) -> ServiceDto_StopMicrophoneStreamResponseDto:
        """Stop the microphone stream."""
        print("[service] stop_stream received")
        print("[service] stop_stream mapping service DTO to outbound DTO")
        port_request_dto = map_service_to_adapter_stop_request(request)

        print("[service] stop_stream calling outbound adapter")
        port_response = await self.controller_port.stop_stream(port_request_dto)

        print(f"[service] stop_stream outbound response success={port_response.success}")
        service_response = map_adapter_to_service_stop_response(port_response)

        print("[service] stop_stream completed")
        return service_response


    async def is_available(self, request: ServiceDto_MicrophoneAvailabilityRequestDto) -> ServiceDto_MicrophoneAvailabilityResponseDto:
        """Check if the microphone is available."""
        print("[service] is_available received")
        print("[service] is_available mapping service DTO to outbound DTO")
        port_request_dto = map_service_to_adapter_availability_request(request)

        print("[service] is_available calling outbound adapter")
        port_response = await self.controller_port.is_available(port_request_dto)

        print(f"[service] is_available outbound response is_available={port_response.is_available}")
        service_response = map_adapter_to_service_availability_response(port_response)

        print("[service] is_available completed")
        return service_response

    def mic_stream(self, request: ServiceDto_GetStreamRequestDto) -> ServiceDto_GetStreamResponseDto:
        """Get the current microphone stream."""
        print("[service] mic_stream received")
        print("[service] mic_stream mapping service DTO to outbound DTO")
        port_request_dto = map_service_to_adapter_get_stream_request(request)

        print("[service] mic_stream calling outbound adapter")
        port_response = self.controller_port.mic_stream(port_request_dto)

        print(f"[service] mic_stream outbound response sample_rate={port_response.sample_rate}")
        service_response = map_adapter_to_service_get_stream_response(port_response)

        print("[service] mic_stream completed")
        return service_response
