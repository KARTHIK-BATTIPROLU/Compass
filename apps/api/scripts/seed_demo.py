import os
from supabase import create_client, Client

supabase: Client = create_client(
    os.getenv("SUPABASE_URL", "http://localhost:8000"),
    os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
)

def seed():
    print("Seeding Demo Data...")
    
    # 1. Faculty User
    f_res = supabase.table("users").upsert({
        "id": "demo-faculty-123",
        "role": "faculty",
        "name": "Prof. Demo",
        "region": "California",
        "language": "English",
        "standard": "Undergrad"
    }).execute()
    print("Seeded Faculty User.")

    # 2. Learner User
    l_res = supabase.table("users").upsert({
        "id": "demo-learner-456",
        "role": "learner",
        "name": "Alex Learner",
        "region": "New York",
        "language": "English",
        "standard": "High School"
    }).execute()
    print("Seeded Learner User.")

    # 3. Learner Weakness Profile
    supabase.table("weakness_profiles").upsert({
        "user_id": "demo-learner-456",
        "topic_id": "Cell Biology",
        "mastery": 0.3,
        "last_seen": "2026-07-15T00:00:00Z"
    }).execute()
    
    supabase.table("weakness_profiles").upsert({
        "user_id": "demo-learner-456",
        "topic_id": "Photosynthesis",
        "mastery": 0.8,
        "last_seen": "2026-07-16T00:00:00Z"
    }).execute()
    print("Seeded Learner Weakness Profiles.")
    
    print("Done!")

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"Error seeding data: {e}. (This may happen if data already exists).")
