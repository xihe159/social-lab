from __future__ import annotations

import os
from functools import lru_cache

from supabase import Client, create_client


class SupabaseConfigError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not service_key:
        raise SupabaseConfigError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured."
        )

    return create_client(url, service_key)
