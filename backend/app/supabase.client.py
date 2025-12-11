# supabase_client.py
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in env")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
# We'll also use the auth REST endpoint to verify tokens when needed.
