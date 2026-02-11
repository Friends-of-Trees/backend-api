from supabase import create_client
from dotenv import load_dotenv
import os

# explicitly load .env from current folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if SUPABASE_URL is None or SUPABASE_SERVICE_KEY is None:
    raise Exception("Supabase env variables not loaded. Check .env file location.")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)
