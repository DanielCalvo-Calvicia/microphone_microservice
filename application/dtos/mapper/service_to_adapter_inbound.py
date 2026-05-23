from .. import adapter_inbound_dtos as adapter_dtos
from .. import services_dtos as service_dtos


# =====================================================================
# FLOW 1: Starting the Microphone Stream
# =====================================================================

def map_service_to_adapter_start_response(
    service_dto: service_dtos.StartMicrophoneStreamResponseDto
) -> adapter_dtos.StartMicrophoneStreamResponseDto:
    """
    Maps a service layer stream response to an inbound adapter response.
    Executed when the service returns a successful start response to the adapter.
    """
    print(f"[mapper:service->inbound] start response sample_rate={service_dto.sample_rate}")
    return adapter_dtos.StartMicrophoneStreamResponseDto(
        stream=service_dto.stream,
        sample_rate=service_dto.sample_rate
    )


# =====================================================================
# FLOW 2: Stopping the Microphone Stream
# =====================================================================

def map_service_to_adapter_stop_response(
    service_dto: service_dtos.StopMicrophoneStreamResponseDto
) -> adapter_dtos.StopMicrophoneStreamResponseDto:
    """
    Maps a service layer stop response to an inbound adapter stop response.
    Executed when the service returns stop confirmation to the adapter.
    """
    print(f"[mapper:service->inbound] stop response success={service_dto.success}")
    return adapter_dtos.StopMicrophoneStreamResponseDto(
        success=service_dto.success
    )


# =====================================================================
# FLOW 3: Checking Microphone Availability
# =====================================================================

def map_service_to_adapter_availability_response(
    service_dto: service_dtos.MicrophoneAvailabilityResponseDto
) -> adapter_dtos.MicrophoneAvailabilityResponseDto:
    """
    Maps a service layer availability response to an inbound adapter availability response.
    Executed when the service returns microphone availability status to the adapter.
    """
    print(f"[mapper:service->inbound] availability response is_available={service_dto.is_available}")
    return adapter_dtos.MicrophoneAvailabilityResponseDto(
        is_available=service_dto.is_available
    )


# =====================================================================
# FLOW 4: Getting the Microphone Stream
# =====================================================================

def map_service_to_adapter_get_stream_response(
    service_dto: service_dtos.GetStreamResponseDto
) -> adapter_dtos.GetStreamResponseDto:
    """
    Maps a service layer get stream response to an inbound adapter get stream response.
    Executed when the service returns the stream data to the adapter.
    """
    print(f"[mapper:service->inbound] get stream response sample_rate={service_dto.sample_rate}")
    return adapter_dtos.GetStreamResponseDto(
        stream=service_dto.stream,
        sample_rate=service_dto.sample_rate
    )
