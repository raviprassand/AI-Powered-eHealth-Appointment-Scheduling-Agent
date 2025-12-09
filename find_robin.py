import requests
import json

BASE_URL = "https://aetab8pjmb.us-east-1.awsapprunner.com"

def find_doctor_id(name_to_find):
    print(f"🔎 Searching for '{name_to_find}' in the live system...\n")
    
    # Fetch ALL doctors
    url = f"{BASE_URL}/table/doctors_registration"
    try:
        response = requests.get(url)
        data = response.json().get("data", [])
        
        found = False
        for doc in data:
            doc_name = doc.get('name', 'Unknown')
            doc_id = doc.get('doctor_id') or doc.get('id')
            
            print(f"   👉 ID: {doc_id} | Name: {doc_name}")
            
            if name_to_find.lower() in doc_name.lower():
                print(f"\n✅ MATCH FOUND! Dr. {doc_name} has ID: {doc_id}")
                found = True
                
        if not found:
            print(f"\n❌ Could not find any doctor named '{name_to_find}'")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_doctor_id("Robin")