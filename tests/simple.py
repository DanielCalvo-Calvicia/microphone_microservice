"""
End-to-end integration test for the Microphone Microservice.

This test is fully self-contained:
    1. Boots the server (composition root → FastAPI → Uvicorn)
    2. Waits for it to be healthy
    3. Runs the full API flow
    4. Shuts the server down gracefully

Usage:
    python tests/simple.py
"""

import asyncio
import sys
import time
from pathlib import Path

# ── Ensure project root is on sys.path ──────────────────
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

import httpx
import uvicorn

from composition_root.containers.container import BuildContainer

# ── Configuration ───────────────────────────────────────
HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"
STREAM_READ_SECONDS = 2  # How long to read audio chunks from each streaming endpoint
STARTUP_TIMEOUT = 10     # Max seconds to wait for the server to become healthy


# ──────────────────────────────────────────────
# SERVER LIFECYCLE
# ──────────────────────────────────────────────

async def start_server() -> tuple[uvicorn.Server, asyncio.Task]:
    """Boot the microservice exactly like main.py does and return
    the server instance + its background task."""

    container = BuildContainer(name="Test Microservice")
    app = container.microphone_dependency.adapter_inbound.get_app

    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)

    task = asyncio.create_task(server.serve())

    # Wait until the server is accepting connections
    async with httpx.AsyncClient(timeout=2.0) as client:
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            try:
                resp = await client.get(f"{BASE_URL}/health")
                if resp.status_code == 200:
                    break
            except httpx.ConnectError:
                pass
            await asyncio.sleep(0.2)
        else:
            raise RuntimeError(
                f"Server did not become healthy within {STARTUP_TIMEOUT}s"
            )

    return server, task


async def stop_server(server: uvicorn.Server, task: asyncio.Task) -> None:
    """Signal the server to shut down and wait for the task to finish."""
    server.should_exit = True
    await task


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def print_header(title: str) -> None:
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


def print_result(label: str, success: bool, detail: str = "") -> None:
    icon = "✅" if success else "❌"
    msg = f"  {icon} {label}"
    if detail:
        msg += f"  →  {detail}"
    print(msg)


async def read_stream_for(response: httpx.Response, seconds: float) -> int:
    """Read bytes from a streaming response for a limited duration.
    Returns total bytes read."""
    total_bytes = 0
    deadline = time.monotonic() + seconds

    async for chunk in response.aiter_bytes(chunk_size=4096):
        total_bytes += len(chunk)
        if time.monotonic() >= deadline:
            break

    return total_bytes


# ──────────────────────────────────────────────
# TEST STEPS
# ──────────────────────────────────────────────

async def test_health(client: httpx.AsyncClient) -> bool:
    print_header("1. Health Check  →  GET /health")
    resp = await client.get(f"{BASE_URL}/health")
    body = resp.json()
    ok = resp.status_code == 200 and body.get("status") == "success"
    print_result("Health", ok, f"status={resp.status_code}  body={body}")
    return ok


async def test_available(client: httpx.AsyncClient, step: str, expected: bool) -> bool:
    print_header(f"{step}. Availability Check  →  GET /available  (expect={expected})")
    resp = await client.get(f"{BASE_URL}/available")
    body = resp.json()
    actual = body.get("data")
    ok = resp.status_code == 200 and actual == expected
    print_result("Available", ok, f"expected={expected}  actual={actual}")
    return ok


async def test_start(client: httpx.AsyncClient) -> bool:
    print_header("3. Start Microphone  →  POST /start  (streaming response)")
    async with client.stream(
        "POST",
        f"{BASE_URL}/start",
        json={"sample_rate": 16000, "channels": 1, "chunk_size": 1024},
    ) as resp:
        sample_rate = resp.headers.get("x-sample-rate", "?")
        status_hdr = resp.headers.get("x-status", "?")

        total = await read_stream_for(resp, STREAM_READ_SECONDS)

    ok = resp.status_code == 200 and total > 0
    print_result(
        "Start + Stream",
        ok,
        f"status={resp.status_code}  bytes_read={total}  "
        f"sample_rate={sample_rate}  x-status={status_hdr}",
    )
    return ok


async def test_stream(client: httpx.AsyncClient) -> bool:
    print_header("5. Read Existing Stream  →  GET /stream  (streaming response)")
    async with client.stream("GET", f"{BASE_URL}/stream") as resp:
        if resp.status_code != 200:
            body_bytes = await resp.aread()
            print_result("Stream", False, f"status={resp.status_code}  body={body_bytes.decode()}")
            return False

        sample_rate = resp.headers.get("x-sample-rate", "?")
        total = await read_stream_for(resp, STREAM_READ_SECONDS)

    ok = total > 0
    print_result(
        "Stream",
        ok,
        f"status={resp.status_code}  bytes_read={total}  sample_rate={sample_rate}",
    )
    return ok


async def test_stop(client: httpx.AsyncClient) -> bool:
    print_header("6. Stop Microphone  →  POST /stop")
    resp = await client.post(f"{BASE_URL}/stop", json={})
    body = resp.json()
    ok = resp.status_code == 200 and body.get("status") == "success"
    print_result("Stop", ok, f"status={resp.status_code}  body={body}")
    return ok


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

async def run_tests() -> None:
    print("\n" + "=" * 50)
    print("  Microphone Microservice  –  E2E Test")
    print("=" * 50)

    # ── Boot the server ──
    print_header("🚀 Starting server...")
    server, server_task = await start_server()
    print_result("Server", True, f"listening on {BASE_URL}")

    results: list[bool] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Health
            results.append(await test_health(client))

            # 2. Available (should be False before start)
            results.append(await test_available(client, "2", expected=False))

            # 3. Start (streams audio for STREAM_READ_SECONDS then disconnects)
            results.append(await test_start(client))

            # 4. Available (should be True after start)
            results.append(await test_available(client, "4", expected=True))

            # 5. Stream (read from existing stream)
            results.append(await test_stream(client))

            # 6. Stop
            results.append(await test_stop(client))

            # 7. Available (should be False after stop)
            results.append(await test_available(client, "7", expected=False))

    finally:
        # ── Shut down the server ──
        print_header("🛑 Stopping server...")
        await stop_server(server, server_task)
        print_result("Server", True, "shut down gracefully")

    # ── Summary ──
    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 50)
    if passed == total:
        print(f"  ✅  ALL PASSED  ({passed}/{total})")
    else:
        print(f"  ❌  FAILURES  ({passed}/{total} passed)")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(run_tests())