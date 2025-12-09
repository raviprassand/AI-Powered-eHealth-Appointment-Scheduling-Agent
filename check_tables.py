import requests

# Your API Base URL
BASE_URL = "https://aetab8pjmb.us-east-1.awsapprunner.com"

def check_table(table_name):
    url = f"{BASE_URL}/table/{table_name}"
    print(f"🔎 Checking table: '{table_name}' ...", end=" ")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ FOUND!")
        else:
            print(f"❌ Not Found (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")

# Common guesses for table names
possible_names = [
    "patient_registration",  # The one causing the error
    "patients_registration", # Plural?
    "patient",               # Simple?
    "patients",              # Simple Plural?
    "registration",          # Generic?
    "doctors_registration"   # We know this one exists
]

print("--- DIAGNOSTIC START ---")
for name in possible_names:
    check_table(name)
print("--- DIAGNOSTIC END ---")