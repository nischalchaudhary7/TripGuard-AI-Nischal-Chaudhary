import httpx


def build_client(timeout: float) -> httpx.AsyncClient:
    headers = {
        "User-Agent": "TripGuardAI/0.1 contact@example.com",
        "Accept": "application/geo+json, application/json, text/csv, text/plain;q=0.8",
    }
    return httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True)

