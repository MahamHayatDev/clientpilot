import time

import httpx
from supabase import create_client, Client, ClientOptions

from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY


class RetryTransport(httpx.HTTPTransport):
    """Retry read requests when Supabase drops the connection."""

    def handle_request(self, request):
        attempts = 3 if request.method in ("GET", "HEAD") else 1
        for attempt in range(attempts):
            try:
                return super().handle_request(request)
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.WriteError):
                if attempt == attempts - 1:
                    raise
                time.sleep(0.3)


# No connection reuse and no HTTP/2: every request gets a fresh connection.
_transport = RetryTransport(
    http2=False,
    retries=3,
    limits=httpx.Limits(max_keepalive_connections=0),
)
_http_client = httpx.Client(transport=_transport, timeout=httpx.Timeout(30.0))

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    options=ClientOptions(httpx_client=_http_client),
)
