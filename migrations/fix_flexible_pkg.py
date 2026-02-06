from api.database import get_supabase_client

def fix():
    print("Connecting to DB...")
    supabase = get_supabase_client()
    
    # Check for Flexible package by flag
    print("Checking is_flexible flag...")
    res = supabase.table("subscription_packages").select("*").eq("is_flexible", True).execute()
    
    if res.data:
        print(f"Found {len(res.data)} flexible packages.")
        for p in res.data:
            print(f"- {p['name']} ({p['id']})")
        return

    # Check by Name
    print("Flag missing. Searching by name 'Flexible'...")
    res = supabase.table("subscription_packages").select("*").ilike("name", "%Flexible%").execute()
    
    if res.data:
        pkg = res.data[0]
        print(f"Found compatible package: {pkg['name']} ({pkg['id']})")
        print("Updating is_flexible=True...")
        supabase.table("subscription_packages").update({"is_flexible": True}).eq("id", pkg['id']).execute()
        print("Done.")
    else:
        print("No Flexible package found. Creating...")
        new_pkg = {
            "name": "Flexible",
            "name_ar": "الباقة المرنة",
            "is_default": True,
            "is_flexible": True,
            "is_active": True,
            "price_monthly": 0,
            "price_yearly": 0,
            "sort_order": 1,
            "max_assistants": 0,
            "storage_mb": 50,
            "ai_words_monthly": 5000,
            "features": ["دفع حسب الاستخدام"]
        }
        supabase.table("subscription_packages").insert(new_pkg).execute()
        print("Created new Flexible package.")

if __name__ == "__main__":
    try:
        fix()
    except Exception as e:
        print(f"Error: {e}")
