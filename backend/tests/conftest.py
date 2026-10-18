import os

# Dummy values so tests never touch your real Supabase project or Gemini key.
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("MODEL_NAME", "gemini-3.5-flash-lite")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault(
    "SUPABASE_SERVICE_KEY",
    "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoic2VydmljZSJ9.c2lnbmF0dXJl",
)
os.environ.setdefault("API_KEY", "test-api-key-for-unit-tests-only")
os.environ.setdefault("ENVIRONMENT", "development")