from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from fastapi import FastAPI


class PIIRedactionSpanProcessor(BatchSpanProcessor):
    def on_end(self, span):
        if span.attributes:
            for key in list(span.attributes.keys()):
                if "email" in key.lower() or "password" in key.lower() or "token" in key.lower():
                    span.attributes[key] = "***REDACTED***"
        super().on_end(span)


def setup_telemetry(
    app: FastAPI,
    app_name: str = "systemforge-backend",
    otlp_endpoint: str = "",
):
    if not otlp_endpoint.strip():
        return trace.get_tracer(app_name)

    provider = TracerProvider()

    exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    processor = PIIRedactionSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    RedisInstrumentor().instrument()

    return trace.get_tracer(app_name)
