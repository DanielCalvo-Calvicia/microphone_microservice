import asyncio
import signal
import uvicorn

from composition_root.containers.container import BuildContainer
from infrastructure.outbound.windows_sounddevice import MicrophoneAdapter
from application.dtos.adapter_outbound_dtos import StopMicrophoneStreamRequestDto

NAME: str = "Microphone Microservice"

async def setup() -> None:    

    print("\n" + "="*60)
    print(f" {NAME} - Starting Server")
    print("="*60)

    print("[setup] Building application container")
    container = BuildContainer(name=NAME)
    
    # We retrieve the FastAPI app instance from the inbound adapter
    print("[setup] Retrieving FastAPI app from inbound adapter")
    app = container.microphone_dependency.adapter_inbound.get_app
    
    print(f"Host: 127.0.0.1")
    print(f"Port: 8000")

    # We configure and create a uvicorn Server instance
    print("[setup] Creating Uvicorn config and server")
    config = uvicorn.Config(app, host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)

    print("Application started. Waiting for shutdown signal (Ctrl+C)...")
    
    # Uvicorn's serve() method is an asynchronous blocking call that automatically 
    # listens for termination signals (like Ctrl+C) and shuts down gracefully.
    print("[setup] Entering Uvicorn serve loop")
    await server.serve()
    
    # Once Uvicorn has finished shutting down, we execute our custom cleanup logic.
    print("[setup] Uvicorn stopped; starting cleanup")
    await _cleanup(container)
    


async def _cleanup(container) -> None:
    print("[cleanup] Inspecting outbound adapter state")
    adapter = container.microphone_dependency.adapter_outbound

    if isinstance(adapter, MicrophoneAdapter):
        print(f"[cleanup] MicrophoneAdapter started={adapter.started}")
        if adapter.started:
            print("Stopping microphone stream before exit...")
            await adapter.stop_stream(StopMicrophoneStreamRequestDto())

    print("Cleanup finished.")
