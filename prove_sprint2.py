import os
import sys
import time
import json
import uuid
import httpx
from dotenv import load_dotenv

# Load env
env_path = os.path.join(os.path.dirname(__file__), "apps", "api", ".env")
load_dotenv(env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
API_URL = "http://127.0.0.1:8002"

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_KEY:
    print("FAIL: Missing Supabase environment variables.")
    sys.exit(1)

print("1. Creating test user to get JWT...")
email = f"test_{uuid.uuid4().hex[:8]}@demo.com"
password = "TestPassword123!"

# Use supabase-py to create confirmed user and sign in
from supabase import create_client
sb_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
try:
    sb_admin.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    # Now sign in to get token
    sb_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    auth_res = sb_anon.auth.sign_in_with_password({"email": email, "password": password})
    access_token = auth_res.session.access_token
    user_id = auth_res.user.id
except Exception as e:
    print(f"FAIL: Admin signup failed - {e}")
    sys.exit(1)

print(f"2. Creating mock session for user {user_id}...")
# Use service key to bypass RLS for inserting a session if user doesn't exist in public.users
db_url = f"{SUPABASE_URL}/rest/v1/sessions"
db_headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# First ensure user exists in public.users
httpx.post(f"{SUPABASE_URL}/rest/v1/users", headers=db_headers, json={
    "id": user_id,
    "email": email,
    "role": "learner",
    "name": "Test User"
})

res = httpx.post(db_url, headers=db_headers, json={
    "user_id": user_id,
    "title": "Test Proof Session",
    "class_level": "Grade 10"
})

if res.status_code >= 400:
    print(f"FAIL: Session creation failed - {res.text}")
    sys.exit(1)

session_id = res.json()[0]["id"]

print(f"3. Querying /api/chat/stream for session {session_id}...")
stream_url = f"{API_URL}/api/chat/stream"
stream_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
payload = {
    "session_id": session_id,
    "prompt": "Create 2 flashcards about photosynthesis",
    "modes": ["flashcards"]
}

try:
    r = httpx.post(stream_url, headers=stream_headers, json=payload, timeout=300.0)
    if r.status_code >= 400:
        print(f"FAIL: Stream request rejected - HTTP {r.status_code}")
        sys.exit(1)
        
    print("   Response received...")
    artifacts_data = None
    for line in r.text.splitlines():
        if line.startswith("data: "):
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                event = json.loads(data_str)
                if event.get("type") == "artifacts":
                    artifacts_data = event.get("data", [])
            except Exception:
                pass
except Exception as e:
    print(f"FAIL: Stream error - {e}")
    sys.exit(1)

if not artifacts_data:
    print("FAIL: No artifacts emitted from stream. Raw response:")
    print(r.text)
    sys.exit(1)

flashcard_art = next((a for a in artifacts_data if a.get("type") == "flashcards"), None)
if not flashcard_art:
    print("FAIL: Flashcards artifact not found in response.")
    sys.exit(1)

download_url = flashcard_art.get("download_url")
if not download_url:
    print("FAIL: download_url not attached to artifact.")
    sys.exit(1)

print(f"4. Testing download_url: {download_url}")
export_url = f"{API_URL}{download_url}"
exp_res = httpx.get(export_url, headers={"Authorization": f"Bearer {access_token}"})

if exp_res.status_code >= 400:
    print(f"FAIL: Export endpoint returned {exp_res.status_code} - {exp_res.text}")
    sys.exit(1)

content_type = exp_res.headers.get("Content-Type", "")
if "csv" not in content_type:
    print(f"FAIL: Expected CSV content type, got {content_type}")
    sys.exit(1)

csv_content = exp_res.text
if "Front" not in csv_content or "Back" not in csv_content:
    print("FAIL: CSV does not look like valid flashcards.")
    sys.exit(1)

print("\n--- CSV Output Preview ---")
print(csv_content[:200])
print("--------------------------\n")

print("PASS: Harness completed successfully!")
sys.exit(0)
