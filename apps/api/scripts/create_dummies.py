import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

def create_dummies():
    print("Creating dummy accounts...")
    try:
        t_res = supabase.auth.admin.create_user({
            "email": "teach@gmail.com",
            "password": "123456",
            "email_confirm": True
        })
        supabase.table("users").upsert({
            "id": t_res.user.id,
            "role": "faculty",
            "name": "Prof. Teach",
            "region": "California",
            "language": "English",
            "standard": "High School"
        }).execute()
        print("Created teach@gmail.com")
    except Exception as e:
        print(f"Teacher creation error: {e}")

    try:
        s_res = supabase.auth.admin.create_user({
            "email": "stud@gmail.com",
            "password": "123456",
            "email_confirm": True
        })
        supabase.table("users").upsert({
            "id": s_res.user.id,
            "role": "learner",
            "name": "Alex Stud",
            "region": "California",
            "language": "English",
            "standard": "High School"
        }).execute()
        
        # Give student some weakness profiles for the demo
        supabase.table("weakness_profiles").upsert({
            "user_id": s_res.user.id,
            "topic_id": "Transformer Architecture",
            "mastery": 0.2,
            "last_seen": "2026-07-15T00:00:00Z"
        }).execute()
        print("Created stud@gmail.com")
    except Exception as e:
        print(f"Student creation error: {e}")

if __name__ == "__main__":
    create_dummies()
