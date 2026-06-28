from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

def get_client() -> Client:
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        return create_client(url, key)
    except Exception as e:
        raise RuntimeError(f"Supabase connection failed: {e}")

def save_message(user_id: str, role: str, message: str):
    try:
        client = get_client()
        client.table("conversations").insert({
            "user_id": user_id,
            "role": role,
            "message": message
        }).execute()
    except Exception as e:
        raise RuntimeError(f"Save failed: {e}")

def load_history(user_id: str, limit: int = 10) -> list:
    try:
        client = get_client()
        response = client.table("conversations")\
            .select("role, message")\
            .eq("user_id", user_id)\
            .order("timestamp", desc=False)\
            .limit(limit)\
            .execute()
        return [{"role": row["role"], "content": row["message"]} for row in response.data]
    except Exception as e:
        return []

def clear_history(user_id: str):
    try:
        client = get_client()
        client.table("conversations")\
            .delete()\
            .eq("user_id", user_id)\
            .execute()
    except Exception as e:
        raise RuntimeError(f"Clear failed: {e}")