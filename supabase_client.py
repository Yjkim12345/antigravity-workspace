import os
import sys

# Ensure this path is added to allow relative imports if run from elsewhere
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not url or not key:
    print("WARNING: Supabase URL or Key not found in .env file.")

# Create a global supabase client
db: Client = create_client(url, key) if url and key else None
