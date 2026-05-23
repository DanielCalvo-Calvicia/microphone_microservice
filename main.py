

import asyncio

from composition_root.setup.setup import setup

if __name__ == "__main__":
    print("[main] Starting microphone microservice process")
    try:
        asyncio.run(setup())
        print("[main] Microphone microservice process exited normally")
    except KeyboardInterrupt:
        print("[main] Keyboard interrupt received. Exiting.")
