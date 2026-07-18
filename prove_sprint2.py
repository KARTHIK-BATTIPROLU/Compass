import os
import sys
import time
import json
import uuid
import httpx
from dotenv import load_dotenv

# Windows consoles default to cp1252, which can't encode characters like
# subscript digits (e.g. CO2) that show up in generated content — force UTF-8
# so a print() never crashes the harness after a successful request.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

# ── 5. Wikimedia image fallback ──────────────────────────────────────────────
print("5. Testing Wikimedia image search...")
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "api"))
from agent.tools.images import search_wikimedia_images

wiki_results = asyncio.run(search_wikimedia_images("human heart anatomy", max_results=3))
if not wiki_results:
    print("FAIL: Wikimedia image search returned no results.")
    sys.exit(1)
if not wiki_results[0].get("url") or not wiki_results[0].get("license"):
    print("FAIL: Wikimedia result missing url/license fields.")
    sys.exit(1)
print(f"   OK: {len(wiki_results)} image(s), first={wiki_results[0]['title']!r}")

# ── 6. Semantic Scholar ───────────────────────────────────────────────────────
print("6. Testing Semantic Scholar search...")
from agent.tools.search import search_semantic_scholar

# The unauthenticated endpoint shares one global rate-limit pool across all
# callers, so a 429 here reflects third-party load, not our code. Probe first
# so a real rate limit degrades gracefully (WARN) instead of masquerading as
# our bug (FAIL) — but any other failure mode (bad response shape, exception,
# a *quiet* empty result when the API is actually healthy) still fails hard.
probe = httpx.get(
    "https://api.semanticscholar.org/graph/v1/paper/search",
    params={"query": "test", "limit": 1, "fields": "title"},
    timeout=10.0,
)
if probe.status_code == 429:
    print("   WARN: Semantic Scholar is rate-limiting unauthenticated requests right now "
          "(shared global quota — outside this app's control). Verifying the wrapper "
          "handles it without crashing (its own built-in retry may still recover)...")
    degraded = asyncio.run(search_semantic_scholar("test query", limit=1))
    if degraded and not degraded[0].get("title"):
        print(f"FAIL: search_semantic_scholar returned malformed data: {degraded}")
        sys.exit(1)
    if degraded:
        print(f"   OK: search_semantic_scholar recovered via its own retry — {len(degraded)} result(s).")
    else:
        print("   OK: search_semantic_scholar degrades to [] cleanly under rate limiting (no crash).")
else:
    scholar_results = asyncio.run(search_semantic_scholar("transformer neural network architecture", limit=3))
    if not scholar_results:
        print("FAIL: Semantic Scholar search returned no results (and the API is not rate-limited).")
        sys.exit(1)
    if not scholar_results[0].get("title"):
        print("FAIL: Semantic Scholar result missing title field.")
        sys.exit(1)
    print(f"   OK: {len(scholar_results)} paper(s), first={scholar_results[0]['title']!r}")

# ── 7. Anki .apkg download (embedded in the flashcards artifact from step 3) ──
print("7. Testing Anki .apkg download...")
import re

anki_match = re.search(r'"download_url":\s*"(/api/download/anki/[^"]+)"', flashcard_art.get("content", ""))
if not anki_match:
    print("FAIL: No embedded Anki download_url found in flashcards artifact content.")
    sys.exit(1)
anki_res = httpx.get(f"{API_URL}{anki_match.group(1)}", headers={"Authorization": f"Bearer {access_token}"})
if anki_res.status_code >= 400:
    print(f"FAIL: Anki download failed - HTTP {anki_res.status_code}")
    sys.exit(1)
if anki_res.content[:2] != b"PK":  # .apkg is a zip container
    print("FAIL: Anki .apkg response does not look like a valid zip file.")
    sys.exit(1)
print(f"   OK: .apkg downloaded, {len(anki_res.content)} bytes")

# ── 8. Quiz-results ownership enforcement (403 for non-owners) ───────────────
print("8. Testing quiz-results ownership enforcement...")
teacher_email = f"teacher_{uuid.uuid4().hex[:8]}@demo.com"
sb_admin.auth.admin.create_user({"email": teacher_email, "password": password, "email_confirm": True})
teacher_auth = sb_anon.auth.sign_in_with_password({"email": teacher_email, "password": password})
teacher_token = teacher_auth.session.access_token
teacher_id = teacher_auth.user.id

httpx.post(f"{SUPABASE_URL}/rest/v1/users", headers=db_headers, json={
    "id": teacher_id, "email": teacher_email, "role": "faculty", "name": "Teacher"
})
teacher_session_res = httpx.post(db_url, headers=db_headers, json={
    "user_id": teacher_id, "title": "Teacher Quiz Session", "class_level": "Grade 10"
})
if teacher_session_res.status_code >= 400:
    print(f"FAIL: Teacher session creation failed - {teacher_session_res.text}")
    sys.exit(1)
teacher_session_id = teacher_session_res.json()[0]["id"]

quiz_payload = {"session_id": teacher_session_id, "prompt": "Quiz me on the water cycle", "modes": ["quiz"]}
quiz_r = httpx.post(
    stream_url,
    headers={"Authorization": f"Bearer {teacher_token}", "Content-Type": "application/json"},
    json=quiz_payload,
    timeout=120.0,
)
quiz_artifacts = None
for line in quiz_r.text.splitlines():
    if line.startswith("data: "):
        data_str = line[6:]
        if data_str == "[DONE]":
            break
        try:
            event = json.loads(data_str)
            if event.get("type") == "artifacts":
                quiz_artifacts = event.get("data", [])
        except Exception:
            pass

if not quiz_artifacts:
    print("FAIL: No quiz artifact emitted. Raw response:")
    print(quiz_r.text)
    sys.exit(1)

quiz_art = next((a for a in quiz_artifacts if a.get("type") == "quiz"), None)
if not quiz_art:
    print("FAIL: quiz artifact type not found.")
    sys.exit(1)

token_match = re.search(r'token="([^"]+)"', quiz_art.get("content", ""))
if not token_match:
    print("FAIL: No share token found in quiz artifact content.")
    sys.exit(1)
share_token = token_match.group(1)

# Confirm the quiz actually persisted (this is the FK bug's regression check —
# quiz_wf used to insert artifact_id=<share token> instead of a real artifacts.id,
# which violated the FK and silently dropped the row every time).
get_res = httpx.get(f"{API_URL}/api/quiz/{share_token}")
if get_res.status_code != 200:
    print(f"FAIL: Quiz was not persisted — GET /api/quiz/{{token}} returned {get_res.status_code}. "
          f"The share link is dead.")
    sys.exit(1)

# The ORIGINAL test user (step 1) does not own the teacher's session — must get 403.
forbidden_res = httpx.get(
    f"{API_URL}/api/quiz/{share_token}/results",
    headers={"Authorization": f"Bearer {access_token}"},
)
if forbidden_res.status_code != 403:
    print(f"FAIL: Expected 403 for non-owner quiz-results access, got {forbidden_res.status_code} — {forbidden_res.text}")
    sys.exit(1)
print("   OK: quiz persisted, share link resolves, non-owner correctly received 403 on results")

# ── 9. Quiz submit input caps (oversized name -> 400) ─────────────────────────
print("9. Testing quiz submit input validation...")
submit_url = f"{API_URL}/api/quiz/{share_token}/submit"

oversized_res = httpx.post(submit_url, json={
    "quiz_id": "x",
    "respondent_name": "A" * 200,
    "answers": {"q1": "A"},
    "score": 80,
    "per_topic": {},
})
if oversized_res.status_code != 400:
    print(f"FAIL: Expected 400 for oversized respondent_name, got {oversized_res.status_code} — {oversized_res.text}")
    sys.exit(1)

malformed_res = httpx.post(submit_url, content=b"not json", headers={"Content-Type": "application/json"})
if malformed_res.status_code != 400:
    print(f"FAIL: Expected 400 for malformed body, got {malformed_res.status_code} — {malformed_res.text}")
    sys.exit(1)
print("   OK: oversized respondent_name and malformed body both correctly rejected with 400")

# ── 10. Quiz submit rate limiting (20 rapid submissions -> 429) ───────────────
print("10. Testing quiz submit rate limiting (20 rapid submissions)...")
saw_429 = False
for i in range(20):
    burst_res = httpx.post(submit_url, json={
        "quiz_id": "x",
        "respondent_name": f"Burst{i}",
        "answers": {"q1": "A"},
        "score": 80,
        "per_topic": {},
    })
    if burst_res.status_code == 429:
        saw_429 = True
        break
if not saw_429:
    print("FAIL: Expected a 429 within 20 rapid submissions, never got one.")
    sys.exit(1)
print(f"   OK: rate limit triggered (429) after {i + 1} rapid submissions")

print("PASS: Harness completed successfully!")
sys.exit(0)
