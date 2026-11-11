import time


def stream_headers(action: str, status_text: str, message: str, sample_rate: int) -> dict[str, str]:
    return {
        "X-Sample-Rate": str(sample_rate),
        "X-Action": action,
        "X-Status": status_text,
        "X-Message": message,
        "X-Timestamp": str(time.time()),
    }
