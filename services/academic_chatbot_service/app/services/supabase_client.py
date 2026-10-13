import os
import threading
from typing import Optional, Callable, Any
import httpx
from supabase import create_client, Client, ClientOptions
from app.utils.logger import logger

_supabase_client: Optional[Client] = None
_client_lock = threading.RLock()

RETRYABLE_EXCEPTIONS = (
    httpx.RemoteProtocolError,
    httpx.NetworkError,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.PoolTimeout,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
)

def _is_transient_connection_error(exc: Exception) -> bool:
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True
    msg = str(exc).lower()
    return any(keyword in msg for keyword in ("server disconnected", "connection reset", "remoteprotocolerror", "broken pipe"))

def _create_resilient_httpx_client() -> httpx.Client:
    """
    Creates an httpx.Client configured to prevent stale connection drops:
    - http2=False: Prevents HTTP/2 stream disconnects on idle Cloudflare/Supabase proxies.
    - keepalive_expiry=25.0: Proactively expires idle connections before server timeout (~60s).
    - limits: Configured connection pooling.
    - timeout: 30s read/write timeout, 10s connect timeout.
    """
    limits = httpx.Limits(
        max_keepalive_connections=20,
        max_connections=50,
        keepalive_expiry=25.0,
    )
    timeout = httpx.Timeout(30.0, connect=10.0)
    return httpx.Client(
        http2=False,
        limits=limits,
        timeout=timeout,
        follow_redirects=True,
    )

def reset_supabase_client():
    """
    Closes the existing client/connection pool and clears the singleton.
    """
    global _supabase_client
    with _client_lock:
        if _supabase_client is not None:
            try:
                # Close underlying postgrest httpx session if present
                if hasattr(_supabase_client, "_postgrest") and _supabase_client._postgrest:
                    _supabase_client._postgrest.session.close()
                elif hasattr(_supabase_client, "options") and _supabase_client.options.httpx_client:
                    _supabase_client.options.httpx_client.close()
            except Exception as e:
                logger.debug(f"Error closing supabase httpx_client during reset: {e}")
            _supabase_client = None

def get_supabase_client(force_new: bool = False) -> Optional[Client]:
    """
    Retrieves or creates the Supabase client singleton with resilient HTTP transport.
    If force_new is True, closes the existing client and creates a fresh instance.
    """
    global _supabase_client
    with _client_lock:
        if force_new:
            reset_supabase_client()
        elif _supabase_client is not None:
            return _supabase_client

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_KEY", "")
        if url and key:
            try:
                http_client = _create_resilient_httpx_client()
                options = ClientOptions(httpx_client=http_client)
                _supabase_client = create_client(url, key, options=options)
                return _supabase_client
            except Exception as e:
                logger.exception(f"Failed to create resilient Supabase client: {e}")
        return None

def execute_with_retry(operation: Callable[[Client], Any], max_retries: int = 1) -> Any:
    """
    Executes a Supabase operation callable: operation(supabase).
    If a transient connection drop occurs (e.g. RemoteProtocolError: Server disconnected),
    it resets the client singleton and retries once with a fresh connection pool.
    """
    for attempt in range(max_retries + 1):
        supabase = get_supabase_client()
        if not supabase:
            return None
        try:
            return operation(supabase)
        except Exception as e:
            if attempt < max_retries and _is_transient_connection_error(e):
                logger.warning(
                    f"Supabase connection dropped ({type(e).__name__}: {e}), reconnecting and retrying... (attempt {attempt + 1}/{max_retries + 1})"
                )
                reset_supabase_client()
            else:
                if attempt > 0:
                    logger.error(f"Supabase operation failed after retry: {e}")
                raise
