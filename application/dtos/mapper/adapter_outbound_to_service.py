from .. import adapter_outbound_dtos as adapter_dtos
from .. import services_dtos as service_dtos



# =====================================================================
# FLOW 1: Starting the Microphone Stream
# =====================================================================

def map_adapter_to_service_start_response(
    adapter_dto: adapter_dtos.StartMicrophoneStreamResponseDto
) -> service_dtos.StartMicrophoneStreamResponseDto:
    """
    Maps an outbound adapter stream response back to the service layer response.
    Executed when returning the stream from the adapter back to the core.
    """
    print(f"[mapper:outbound->service] start response sample_rate={adapter_dto.sample_rate}")
    return service_dtos.StartMicrophoneStreamResponseDto(
        stream=adapter_dto.stream,
        sample_rate=adapter_dto.sample_rate
    )



# =====================================================================
# FLOW 2: Stopping the Microphone Stream
# =====================================================================

def map_adapter_to_service_stop_response(
    adapter_dto: adapter_dtos.StopMicrophoneStreamResponseDto
) -> service_dtos.StopMicrophoneStreamResponseDto:
    """
    Maps an outbound adapter stop confirmation to a service layer response.
    """
    print(f"[mapper:outbound->service] stop response success={adapter_dto.success}")
    return service_dtos.StopMicrophoneStreamResponseDto(
        success=adapter_dto.success
    )


# =====================================================================
# FLOW 3: Checking Microphone Availability
# =====================================================================

def map_adapter_to_service_availability_response(
    adapter_dto: adapter_dtos.MicrophoneAvailabilityResponseDto
) -> service_dtos.MicrophoneAvailabilityResponseDto:
    """
    Maps an outbound adapter hardware availability status to a service layer response.
    """
    print(f"[mapper:outbound->service] availability response is_available={adapter_dto.is_available}")
    return service_dtos.MicrophoneAvailabilityResponseDto(
        is_available=adapter_dto.is_available
    )


# =====================================================================
# FLOW 4: Getting the Microphone Stream
# =====================================================================

def map_adapter_to_service_get_stream_response(
    adapter_dto: adapter_dtos.GetStreamResponseDto
) -> service_dtos.GetStreamResponseDto:
    """
    Maps an outbound adapter stream response to a service layer response.
    """
    print(f"[mapper:outbound->service] get stream response sample_rate={adapter_dto.sample_rate}")
    return service_dtos.GetStreamResponseDto(
        stream=adapter_dto.stream,
        sample_rate=adapter_dto.sample_rate
    )
