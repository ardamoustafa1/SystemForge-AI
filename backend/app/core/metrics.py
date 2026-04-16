from __future__ import annotations

from collections import defaultdict
from threading import Lock

_lock = Lock()
_request_count = defaultdict(int)
_request_errors = defaultdict(int)
_request_latency_sum_ms = defaultdict(float)
_worker_events = defaultdict(int)
_worker_queue_lag = defaultdict(float)
_worker_retry_buckets = defaultdict(int)


def observe_request(path: str, method: str, status_code: int, elapsed_ms: int) -> None:
    key = f'{method} {path}'
    with _lock:
        _request_count[key] += 1
        _request_latency_sum_ms[key] += float(elapsed_ms)
        if status_code >= 500:
            _request_errors[key] += 1


def render_prometheus() -> str:
    lines: list[str] = [
        "# HELP sf_http_requests_total Total HTTP requests",
        "# TYPE sf_http_requests_total counter",
    ]
    with _lock:
        for key, value in sorted(_request_count.items()):
            method, path = key.split(" ", 1)
            lines.append(f'sf_http_requests_total{{method="{method}",path="{path}"}} {value}')
        lines.extend(
            [
                "# HELP sf_http_request_errors_total Total HTTP 5xx responses",
                "# TYPE sf_http_request_errors_total counter",
            ]
        )
        for key, value in sorted(_request_errors.items()):
            method, path = key.split(" ", 1)
            lines.append(f'sf_http_request_errors_total{{method="{method}",path="{path}"}} {value}')
        lines.extend(
            [
                "# HELP sf_http_request_latency_ms_sum Sum of request latency in milliseconds",
                "# TYPE sf_http_request_latency_ms_sum counter",
            ]
        )
        for key, value in sorted(_request_latency_sum_ms.items()):
            method, path = key.split(" ", 1)
            lines.append(f'sf_http_request_latency_ms_sum{{method="{method}",path="{path}"}} {value:.2f}')
        lines.extend(
            [
                "# HELP sf_worker_events_total Worker lifecycle events",
                "# TYPE sf_worker_events_total counter",
            ]
        )
        for key, value in sorted(_worker_events.items()):
            worker, event = key.split(" ", 1)
            lines.append(f'sf_worker_events_total{{worker="{worker}",event="{event}"}} {value}')
        lines.extend(
            [
                "# HELP sf_worker_queue_lag Worker queue lag gauge",
                "# TYPE sf_worker_queue_lag gauge",
            ]
        )
        for worker, value in sorted(_worker_queue_lag.items()):
            lines.append(f'sf_worker_queue_lag{{worker="{worker}"}} {value:.2f}')
        lines.extend(
            [
                "# HELP sf_worker_retry_histogram Worker retry histogram buckets",
                "# TYPE sf_worker_retry_histogram counter",
            ]
        )
        for key, value in sorted(_worker_retry_buckets.items()):
            worker, bucket = key.split(" ", 1)
            lines.append(f'sf_worker_retry_histogram{{worker="{worker}",bucket="{bucket}"}} {value}')
    return "\n".join(lines) + "\n"


def observe_worker_event(worker: str, event: str) -> None:
    with _lock:
        _worker_events[f"{worker} {event}"] += 1


def set_worker_queue_lag(worker: str, lag: float) -> None:
    with _lock:
        _worker_queue_lag[worker] = max(0.0, float(lag))


def observe_worker_retry(worker: str, retry_count: int) -> None:
    if retry_count <= 0:
        bucket = "0"
    elif retry_count <= 2:
        bucket = "1-2"
    elif retry_count <= 5:
        bucket = "3-5"
    else:
        bucket = "6+"
    with _lock:
        _worker_retry_buckets[f"{worker} {bucket}"] += 1

