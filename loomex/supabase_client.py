"""
Single shared Supabase client for the whole app.

We use the SERVICE ROLE key here (not the public "anon" key) because every
database call in this project happens on the server, inside our FastAPI
routes — never in the browser. The service role key bypasses Row Level
Security, which is fine because our own route code is what decides what a
visitor is allowed to see or do.

NEVER put the service role key in any file that ships to the browser
(templates, static JS, etc). It only ever lives in environment variables.
"""

import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables. "
        "Copy .env.example to .env for local dev, or set them in the Vercel "
        "project's Environment Variables settings for production."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
