"""Lightweight Prometheus-style metrics for codelab services."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from fastapi import Request
from fastapi.responses import PlainTextResponse


@dataclass
class ServiceMetrics:
    service_name: str
    request_count: int = 0
    error_count: int = 0
    total_latency_seconds: float = 0.0
    path_counts: dict[str, int] = field(default_factory=dict)

    def observe(self, path: str, status_code: int, latency: float) -> None:
        self.request_count += 1
        self.total_latency_seconds += latency
        self.path_counts[path] = self.path_counts.get(path, 0) + 1
        if status_code >= 500:
            self.error_count += 1

    def render(self) -> str:
        avg_latency = self.total_latency_seconds / self.request_count if self.request_count else 0.0
        lines = [
            "# HELP a2a_requests_total Total HTTP requests handled by this service.",
            "# TYPE a2a_requests_total counter",
            f'a2a_requests_total{{service="{self.service_name}"}} {self.request_count}',
            "# HELP a2a_errors_total Total 5xx HTTP responses handled by this service.",
            "# TYPE a2a_errors_total counter",
            f'a2a_errors_total{{service="{self.service_name}"}} {self.error_count}',
            "# HELP a2a_request_latency_seconds_total Total request latency in seconds.",
            "# TYPE a2a_request_latency_seconds_total counter",
            f'a2a_request_latency_seconds_total{{service="{self.service_name}"}} {self.total_latency_seconds:.6f}',
            "# HELP a2a_request_latency_seconds_avg Average request latency in seconds.",
            "# TYPE a2a_request_latency_seconds_avg gauge",
            f'a2a_request_latency_seconds_avg{{service="{self.service_name}"}} {avg_latency:.6f}',
        ]
        for path, count in sorted(self.path_counts.items()):
            safe_path = path.replace('"', "'")
            lines.append(f'a2a_requests_by_path_total{{service="{self.service_name}",path="{safe_path}"}} {count}')
        return "\n".join(lines) + "\n"


def add_metrics(app, service_name: str) -> None:
    """Attach request-latency metrics middleware and a `/metrics` endpoint."""
    metrics = ServiceMetrics(service_name=service_name)

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            metrics.observe(request.url.path, status_code, time.perf_counter() - start)

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics_endpoint() -> str:
        return metrics.render()
